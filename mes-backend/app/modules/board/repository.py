"""Truy vấn cho các màn hình điều hành — mọi câu SQL của `board/` nằm ở đây.

    running_rows(db, limit, offset)        MỘT TRANG bảng lệnh đang chạy, đọc view
    queue_rows(db, station)                hàng chờ một trạm
    at_station_rows(db, station)           lệnh ĐANG nằm trong tay một trạm
    queue_counts(db)                       đếm cả sáu trạm — MỘT câu
    line_rows_of_rounds(db, round_ids)     năng suất chuyền, theo LÔ vòng
    step_totals(db, mo_id)                 cộng dồn thời gian từng bước
    mo_progress(db, mo_id)                 tiến độ một MO

Hai điều đáng biết trước khi sửa file này:

**`QUEUE_SQL` là nguồn DUY NHẤT của hàng chờ.** Cả danh sách (`queue_rows`) lẫn con
số trên badge (`queue_counts`) đều dựng từ nó. Viết câu đếm riêng thì sớm muộn hai
câu trôi khỏi nhau, badge hiện một số mà bấm vào ra số khác — mà không ai báo lỗi.

**Các hàm `*_of_rounds` đọc theo LÔ.** Trước đây `trace` hỏi từng vòng một nên MO
bốn vòng tốn 25 câu SQL. Nay gom `round_id` lại hỏi một lần, còn 10 câu bất kể
bao nhiêu vòng.
"""

from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import date

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.common.config import settings
from app.common.vocab.enums import STEP_NAMES

_CHUNG = """
    SELECT m.code, m.product_name, m.quantity, r.round_no, r.target_qty,
           EXTRACT(EPOCH FROM (now() - prev.accepted_at))::int AS waiting_sec
    FROM mo_round r JOIN manufacturing_order m ON m.id = r.mo_id
    JOIN mo_step prev ON prev.round_id = r.id AND prev.step_no = {prev}
    LEFT JOIN mo_step s ON s.round_id = r.id AND s.step_no = {step}
    WHERE r.closed_at IS NULL AND s.id IS NULL
"""

QUEUE_SQL: dict[int, str] = {
    0: """
        SELECT m.code, m.product_name, m.quantity, r.round_no, r.target_qty,
               EXTRACT(EPOCH FROM (now() - r.opened_at))::int AS waiting_sec
        FROM mo_round r JOIN manufacturing_order m ON m.id = r.mo_id
        LEFT JOIN mo_step s ON s.round_id = r.id AND s.step_no = 0
        WHERE r.closed_at IS NULL AND m.status = 'PROCESSING' AND s.id IS NULL
    """,
    1: """
        SELECT m.code, m.product_name, m.quantity, r.round_no, r.target_qty,
               EXTRACT(EPOCH FROM (now() - w.handed_over_at))::int AS waiting_sec
        FROM mo_round r JOIN manufacturing_order m ON m.id = r.mo_id
        JOIN warehouse_out w ON w.round_id = r.id
        LEFT JOIN mo_step s ON s.round_id = r.id AND s.step_no = 1
        WHERE r.closed_at IS NULL AND s.id IS NULL
    """,
    5: """
        SELECT m.code, m.product_name, m.quantity, r.round_no, r.target_qty,
               m.pcs_per_box, pk.qty_packed,
               EXTRACT(EPOCH FROM (now() - pk.completed_at))::int AS waiting_sec
        FROM mo_round r JOIN manufacturing_order m ON m.id = r.mo_id
        JOIN production p ON p.round_id = r.id
        JOIN packing   pk ON pk.round_id = r.id AND pk.completed_at IS NOT NULL
        LEFT JOIN mo_step s ON s.round_id = r.id AND s.step_no = 5
        WHERE r.closed_at IS NULL AND s.id IS NULL
    """,
    3: """
        SELECT m.code, m.product_name, m.quantity, r.round_no, r.target_qty,
               EXTRACT(EPOCH FROM (now() - q.checked_at))::int AS waiting_sec
        FROM mo_round r JOIN manufacturing_order m ON m.id = r.mo_id
        JOIN mo_step prev ON prev.round_id = r.id AND prev.step_no = 2
        JOIN qc_result q ON q.round_id = r.id AND q.result = 'PASS'
        LEFT JOIN mo_step s ON s.round_id = r.id AND s.step_no = 3
        WHERE r.closed_at IS NULL AND s.id IS NULL
    """,
    **{n: _CHUNG.format(prev=n - 1, step=n) for n in (2, 4)},
}

HOLDING_SQL = """
    SELECT s.step_no, count(*) AS n
    FROM mo_step s
    JOIN mo_round r ON r.id = s.round_id
    JOIN manufacturing_order m ON m.id = r.mo_id
    WHERE s.closed_at IS NULL AND r.closed_at IS NULL
"""

# Lọc theo NGÀY TẠO lệnh, quy về giờ tường của xưởng.
#
# `/board/counts` là ảnh chụp HIỆN TẠI, không phải lịch sử: nó đếm lệnh đang nằm ở
# mỗi trạm ngay lúc hỏi. Bộ lọc này thu hẹp TẬP LỆNH được đếm, chứ không dựng lại
# được tình trạng xưởng của một ngày đã qua — muốn thế phải phát lại nhật ký.
_CREATED_BETWEEN = (
    " AND (CAST(:date_from AS date) IS NULL"
    "      OR timezone(:tz, m.created_at) >= CAST(:date_from AS date))"
    " AND (CAST(:date_to AS date) IS NULL"
    "      OR timezone(:tz, m.created_at) < CAST(:date_to AS date) + 1)"
)

_PAGE = " LIMIT :limit OFFSET :offset"

def _count_of(db: Session, sql: str, params: dict | None = None) -> int:
    """Đếm bằng cách BỌC LẠI chính câu đang dùng, không viết câu đếm riêng.

    Viết riêng thì sớm muộn hai câu trôi khỏi nhau — danh sách một đằng, tổng một nẻo,
    và không ai báo lỗi. Cùng lý lẽ với `QUEUE_SQL` là nguồn duy nhất của hàng chờ.
    """
    return db.scalar(text(f"SELECT count(*) FROM ({sql}) q"), params or {}) or 0

def running_rows(db: Session, *, limit: int, offset: int = 0) -> list[dict]:
    """MỘT TRANG bảng lệnh đang chạy — đọc thẳng view, không tính lại gì ở Python."""
    return [dict(r) for r in db.execute(
        text(f"SELECT * FROM v_round_board ORDER BY code{_PAGE}"),
        {"limit": limit, "offset": offset}).mappings()]

def count_running(db: Session) -> int:
    return _count_of(db, "SELECT 1 FROM v_round_board")

def queue_rows(db: Session, station: int, *, limit: int, offset: int = 0) -> list[dict]:
    """MỘT TRANG hàng chờ của một trạm."""
    sql = QUEUE_SQL[station] + f" ORDER BY m.code{_PAGE}"
    return [dict(r) for r in db.execute(
        text(sql), {"limit": limit, "offset": offset}).mappings()]

def count_queue(db: Session, station: int) -> int:
    return _count_of(db, QUEUE_SQL[station])

AT_STATION_SQL = """
    SELECT m.code, m.product_name, m.quantity, m.pcs_per_box,
           r.round_no, r.target_qty, r.required_sec,
           timezone(:tz, s.accepted_at) AS accepted_at, u.full_name AS accepted_by,
           EXTRACT(EPOCH FROM (now() - s.accepted_at))::int AS holding_sec,
           timezone(:tz, w.handed_over_at) AS handed_over_at, pk.qty_packed,
           timezone(:tz, pk.completed_at) AS packing_done_at,
           q.result::text AS qc_result, timezone(:tz, q.checked_at) AS qc_checked_at
    FROM mo_step s
    JOIN mo_round r ON r.id = s.round_id
    JOIN manufacturing_order m ON m.id = r.mo_id
    JOIN app_user u ON u.id = s.accepted_by
    LEFT JOIN warehouse_out w ON w.round_id = r.id
    LEFT JOIN packing      pk ON pk.round_id = r.id
    LEFT JOIN qc_result    q  ON q.round_id = r.id
    WHERE s.step_no = :station AND s.closed_at IS NULL AND r.closed_at IS NULL
    ORDER BY s.accepted_at, m.code
"""

def at_station_rows(db: Session, station: int, *,
                    limit: int, offset: int = 0) -> list[dict]:
    """Lệnh đã quét nhận ở trạm này và CHƯA đóng bước — tức đang trong tay họ.

    Khác `queue_rows` ở đúng một chỗ, nhưng là chỗ quan trọng nhất với người vận
    hành: hàng đợi là việc CHƯA nhận, cái này là việc ĐANG cầm. Thiếu nó thì quét
    xong lệnh biến mất khỏi màn hình và không ai biết nó đang ở đâu.

    Bước chỉ đóng khi trạm SAU quét nhận (xem `MoStep`), nên `closed_at IS NULL`
    đúng nghĩa là "chưa ai lấy đi".

    Kèm luôn các mốc mà THAO TÁC của trạm cần để biết nút nào còn bấm được:
    `handed_over_at` (trạm 0 đã giao chưa), `qty_packed` và `packing_done_at`
    (trạm 5 nhận bao nhiêu), `qc_result` và `qc_checked_at` (trạm 2 đã kết luận
    chưa). Không có chúng thì màn hình phải đoán, mà đoán sai là hiện nút cho
    việc đã làm rồi.

    Trạm 2 giữ lệnh CẢ SAU KHI ra kết quả — bước chỉ đóng khi Bàn team leader quét
    nhận. Nên "còn trong tay QC" và "chưa có kết quả" là hai chuyện khác nhau, và
    chỉ `qc_result` phân biệt được.
    """
    rows = db.execute(text(AT_STATION_SQL + _PAGE),
                      {"station": station, "tz": settings.tz,
                       "limit": limit, "offset": offset}).mappings()
    return [dict(r) for r in rows]

def count_at_station(db: Session, station: int) -> int:
    return _count_of(db, AT_STATION_SQL, {"station": station, "tz": settings.tz})

def queue_counts(db: Session, *, date_from: date | None = None,
                 date_to: date | None = None) -> tuple[dict[int, int], dict[int, int]]:
    """Hai con số của mỗi trạm: CHỜ NHẬN và ĐANG GIỮ. Hai câu, không phải mười hai.

    Gộp chung thành một số là đánh mất đúng thứ người quản lý cần phân biệt: chờ
    nhận là việc chưa ai đụng vào — có người phải đi quét; đang giữ là việc đang
    chạy — không cần ai làm gì thêm. Một trạm 0 chờ 3 đang giữ và một trạm 3 chờ
    0 đang giữ là hai tình huống trái ngược nhau.

    Nhóm chờ nhận dựng từ chính `QUEUE_SQL` nên con số luôn khớp danh sách của
    `queue_rows` — xem đầu file.
    """
    loc = {"date_from": date_from, "date_to": date_to, "tz": settings.tz}
    parts = [f"SELECT {n} AS step_no, count(*) AS n FROM ({sql}{_CREATED_BETWEEN}) q"
            for n, sql in sorted(QUEUE_SQL.items())]
    waiting_rows = db.execute(text(" UNION ALL ".join(parts)), loc).mappings().all()
    holding_rows = db.execute(
        text(HOLDING_SQL + _CREATED_BETWEEN + " GROUP BY s.step_no"), loc).mappings().all()

    waiting = dict.fromkeys(STEP_NAMES, 0)
    holding = dict.fromkeys(STEP_NAMES, 0)
    for r in waiting_rows:
        waiting[r["step_no"]] += r["n"]
    for r in holding_rows:
        if r["step_no"] in holding:
            holding[r["step_no"]] = r["n"]
    return waiting, holding

def line_rows_of_rounds(db: Session, round_ids: list[uuid.UUID]) -> dict[uuid.UUID, list[dict]]:
    """Năng suất từng chuyền, cho NHIỀU vòng một lần. Vòng chưa có chuyền → thiếu khoá."""
    if not round_ids:
        return {}
    rows = db.execute(
        text(
            """
            SELECT t.round_id, l.code AS line_code, t.wait_sec, t.run_sec,
                   t.current_kind, t.hold_reason_text, t.current_since
            FROM v_line_time t JOIN line l ON l.id = t.line_id
            WHERE t.round_id = ANY(:ids) ORDER BY l.code
            """
        ),
        {"ids": round_ids},
    ).mappings().all()

    theo_vong: dict[uuid.UUID, list[dict]] = defaultdict(list)
    for r in rows:
        d = dict(r)
        theo_vong[d.pop("round_id")].append(d)
    return dict(theo_vong)

def step_totals(db: Session, mo_id: uuid.UUID) -> list[dict]:
    """Thời gian cộng dồn từng bước qua MỌI vòng của một MO."""
    return [dict(t) for t in db.execute(
        text("SELECT step_no, sec, rounds FROM v_step_total WHERE mo_id = :m ORDER BY step_no"),
        {"m": mo_id},
    ).mappings()]

def mo_progress(db: Session, mo_id: uuid.UUID) -> dict:
    """Tiến độ một MO — đọc view, không cộng tay."""
    return dict(db.execute(
        text("SELECT * FROM v_mo_progress WHERE mo_id = :m"), {"m": mo_id}
    ).mappings().one())
