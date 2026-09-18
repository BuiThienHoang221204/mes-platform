"""Mọi câu SQL của `reports/` nằm ở đây.

    mo_progress_rows(db, status, date, limit, offset)   MỘT TRANG tiến độ lệnh, đọc view
    count_mo_progress(db, status, date)                tổng số lệnh sau khi lọc
    hourly_rows(db, bucket, date_from, date_to, codes) sản lượng giờ đã gộp khung

Hai điều đáng biết trước khi sửa file này:

**Cả báo cáo sản lượng giờ là MỘT câu SQL.** Không có vòng lặp nào hỏi từng lệnh,
không có lượt hỏi thêm nào để tra mã lệnh từ `round_id` — `manufacturing_order` nối
sẵn trong cùng câu. 100 lệnh × 30 ngày vẫn đúng một lượt đi về.

**`bounded` khai MATERIALIZED là có chủ ý.** Ba thứ cùng đọc nó: số đã gộp theo
khung, số dòng thiếu định mức, và số dòng ghi ngoài giờ. Để Postgres tự nội tuyến
CTE thì nó quét `hourly_output` ba lần cho cùng một khoảng ngày.

**Vì sao ba số đó không tách thành câu riêng:** dòng thiếu định mức bị loại khỏi
phần gộp, nên nếu cả khoảng ngày chỉ toàn dòng thiếu thì câu gộp trả về RỖNG — và
con số "đã bỏ n dòng" biến mất đúng lúc nó cần nhất. `tally LEFT JOIN grouped` giữ
được nó: `tally` luôn có đúng một dòng.
"""

from __future__ import annotations

from datetime import date

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.common.config import settings
from app.modules.reports import shift

_PROGRESS_SQL = """
    SELECT m.code, m.product_name, m.status::text AS status,
           v.quantity, v.qty_done, v.qty_remain,
           v.qty_ok_total, v.qty_ng_total, v.qty_short_total, v.rounds_done
    FROM v_mo_progress v
    JOIN manufacturing_order m ON m.id = v.mo_id
    WHERE (CAST(:status AS text) IS NULL OR m.status::text = CAST(:status AS text))
      {date_filter}
    ORDER BY v.qty_done::numeric / NULLIF(m.quantity, 0) DESC NULLS LAST, m.code
    LIMIT :limit OFFSET :offset
"""

_PROGRESS_COUNT_SQL = """
    SELECT count(*) FROM manufacturing_order m
    WHERE (CAST(:status AS text) IS NULL OR m.status::text = CAST(:status AS text))
      {date_filter}
"""

_CREATED_BETWEEN = """
      AND (CAST(:date_from AS date) IS NULL
           OR timezone(:tz, m.created_at) >= CAST(:date_from AS date))
      AND (CAST(:date_to AS date) IS NULL
           OR timezone(:tz, m.created_at) < CAST(:date_to AS date) + INTERVAL '1 day')
"""


def _date_clause(date_from: date | None, date_to: date | None) -> str:
    return _CREATED_BETWEEN if date_from or date_to else ""


def _date_params(date_from: date | None, date_to: date | None) -> dict:
    return {"date_from": date_from, "date_to": date_to, "tz": settings.tz}


def mo_progress_rows(db: Session, *, status: str | None, limit: int, offset: int = 0,
                     date_from: date | None = None,
                     date_to: date | None = None) -> list[dict]:
    sql = _PROGRESS_SQL.format(date_filter=_date_clause(date_from, date_to))
    rows = db.execute(
        text(sql),
        {"status": status, "limit": limit, "offset": offset,
         **_date_params(date_from, date_to)},
    ).mappings().all()
    return [dict(r) for r in rows]


def count_mo_progress(db: Session, *, status: str | None,
                      date_from: date | None = None,
                      date_to: date | None = None) -> int:
    sql = _PROGRESS_COUNT_SQL.format(date_filter=_date_clause(date_from, date_to))
    return db.scalar(text(sql), {"status": status, **_date_params(date_from, date_to)}) or 0

def _bin_expr(bucket: int, col: str) -> str:
    """Biểu thức SQL đưa một `slot_hour` về giờ BẮT ĐẦU của khung chứa nó.

    Sinh TỪ `shift.bins_of()` chứ không viết tay `CASE` song song — hai bản viết
    tay thì đổi giờ làm là chúng trôi khỏi nhau mà không test nào đỏ.

    Xét theo giờ BẮT ĐẦU giảm dần chứ không theo giờ kết thúc: giờ rơi vào khe
    nghỉ trưa (12:00 ở khung 4 giờ) phải về khung buổi sáng liền trước, xét theo
    giờ kết thúc thì nó nhảy sang buổi chiều.
    """
    bins = shift.bins_of(bucket)
    if len(bins) == 1:
        return str(int(bins[0][0]))
    arms = " ".join(f"WHEN {col} >= {int(s)} THEN {int(s)}" for s, _ in reversed(bins[1:]))
    return f"CASE {arms} ELSE {int(bins[0][0])} END"

def _inside_expr(bucket: int, col: str) -> str:
    """Vế đúng khi giờ thô nằm TRONG một khung thật — phủ định nó là `folded`."""
    return " OR ".join(
        f"({col} >= {int(s)} AND {col} < {int(e)})" for s, e in shift.merged_ranges(bucket)
    )

_HOURLY_SQL = """
WITH bounded AS MATERIALIZED (
    SELECT m.code       AS code,
           h.work_date  AS work_date,
           h.slot_hour  AS slot_hour,
           h.qty        AS qty,
           h.target_qty AS target_qty,
           h.headcount  AS headcount
    FROM hourly_output h
    JOIN mo_round r            ON r.id = h.round_id
    JOIN manufacturing_order m ON m.id = r.mo_id
    WHERE h.work_date BETWEEN :date_from AND :date_to
      AND (CAST(:codes AS text[]) IS NULL OR m.code = ANY (CAST(:codes AS text[])))
),
tally AS (
    SELECT
        count(*) FILTER (WHERE target_qty IS NULL OR target_qty <= 0)       AS skipped_rows,
        count(*) FILTER (WHERE target_qty IS NOT NULL AND target_qty > 0
                           AND NOT ({inside}))                              AS folded_rows
    FROM bounded
),
grouped AS (
    SELECT code,
           work_date + make_interval(hours => {bin}) AS at,
           sum(qty)::int                             AS qty,
           sum(target_qty)::int                      AS target_qty,
           sum(headcount)::int                       AS headcount,
           count(*)::int                             AS slots
    FROM bounded
    WHERE target_qty IS NOT NULL AND target_qty > 0
    GROUP BY 1, 2
)
SELECT t.skipped_rows::int AS skipped_rows,
       t.folded_rows::int  AS folded_rows,
       g.code, g.at, g.qty, g.target_qty, g.headcount, g.slots
FROM tally t
LEFT JOIN grouped g ON true
ORDER BY g.at, g.code
"""

def hourly_rows(
    db: Session,
    *,
    bucket: int,
    date_from: date,
    date_to: date,
    codes: list[str] | None,
) -> list[dict]:
    """Sản lượng giờ đã gộp khung — MỘT lượt đi về, không phụ thuộc số lệnh."""
    sql = _HOURLY_SQL.format(
        inside=_inside_expr(bucket, "slot_hour"),
        bin=_bin_expr(bucket, "slot_hour"),
    )
    rows = db.execute(
        text(sql),
        {"date_from": date_from, "date_to": date_to, "codes": codes},
    ).mappings().all()
    return [dict(r) for r in rows]
