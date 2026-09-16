"""Truy vấn cho các màn hình điều hành — mọi câu SQL của `board/` nằm ở đây.

    running_rows(db)                       bảng lệnh đang chạy, đọc view
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

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.common.vocab.enums import STEP_NAMES

# ── Hàng chờ từng trạm ──────────────────────────────────────────────────────
# Trạm 0, 1, 5 có điều kiện riêng; ba trạm còn lại theo cùng một khuôn: đã xong
# bước trước, chưa nhận bước này. `{prev}` và `{step}` thay bằng số ngay khi dựng
# — chúng là int trong 0–5, không phải dữ liệu người dùng.
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
               pk.qty_packed,
               EXTRACT(EPOCH FROM (now() - pk.completed_at))::int AS waiting_sec
        FROM mo_round r JOIN manufacturing_order m ON m.id = r.mo_id
        JOIN production p ON p.round_id = r.id
        JOIN packing   pk ON pk.round_id = r.id AND pk.completed_at IS NOT NULL
        LEFT JOIN mo_step s ON s.round_id = r.id AND s.step_no = 5
        WHERE r.closed_at IS NULL AND s.id IS NULL
    """,
    # Trạm 3 KHÔNG theo khuôn chung: phải có kết quả QC ĐẠT, không chỉ là "QC đã
    # nhận". `guard_can_accept` chặn đúng chuyện này rồi, nhưng nếu hàng đợi vẫn
    # liệt kê thì Bàn team leader nhìn thấy lệnh, quét vào, và ăn lỗi — màn hình
    # hứa một đằng, hệ thống làm một nẻo.
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

# Kho còn nhóm thứ hai: đã quét nhận nhưng CHƯA bàn giao — hàng vẫn nằm ở kho,
# vẫn cần người làm tiếp. Bỏ nhóm này thì badge hiện 0 trong khi kho còn hàng.
CHO_BAN_GIAO_SQL = """
    SELECT count(*) FROM mo_round r
    JOIN mo_step s ON s.round_id = r.id AND s.step_no = 0
    LEFT JOIN warehouse_out w ON w.round_id = r.id
    WHERE r.closed_at IS NULL AND w.round_id IS NULL
"""


def running_rows(db: Session) -> list[dict]:
    """Bảng lệnh đang chạy — đọc thẳng view, không tính lại gì ở Python."""
    return [dict(r) for r in
            db.execute(text("SELECT * FROM v_round_board ORDER BY code")).mappings()]


def queue_rows(db: Session, station: int) -> list[dict]:
    """Hàng chờ của một trạm."""
    sql = QUEUE_SQL[station] + " ORDER BY m.code"
    return [dict(r) for r in db.execute(text(sql)).mappings()]


AT_STATION_SQL = """
    SELECT m.code, m.product_name, m.quantity, m.pcs_per_box,
           r.round_no, r.target_qty,
           s.accepted_at, u.full_name AS accepted_by,
           EXTRACT(EPOCH FROM (now() - s.accepted_at))::int AS holding_sec,
           w.handed_over_at, pk.qty_packed, pk.completed_at AS packing_done_at
    FROM mo_step s
    JOIN mo_round r ON r.id = s.round_id
    JOIN manufacturing_order m ON m.id = r.mo_id
    JOIN app_user u ON u.id = s.accepted_by
    LEFT JOIN warehouse_out w ON w.round_id = r.id
    LEFT JOIN packing      pk ON pk.round_id = r.id
    WHERE s.step_no = :station AND s.closed_at IS NULL AND r.closed_at IS NULL
    ORDER BY s.accepted_at
"""


def at_station_rows(db: Session, station: int) -> list[dict]:
    """Lệnh đã quét nhận ở trạm này và CHƯA đóng bước — tức đang trong tay họ.

    Khác `queue_rows` ở đúng một chỗ, nhưng là chỗ quan trọng nhất với người vận
    hành: hàng đợi là việc CHƯA nhận, cái này là việc ĐANG cầm. Thiếu nó thì quét
    xong lệnh biến mất khỏi màn hình và không ai biết nó đang ở đâu.

    Bước chỉ đóng khi trạm SAU quét nhận (xem `MoStep`), nên `closed_at IS NULL`
    đúng nghĩa là "chưa ai lấy đi".

    Kèm luôn ba mốc mà THAO TÁC của trạm cần để biết nút nào còn bấm được:
    `handed_over_at` (trạm 0 đã giao chưa), `qty_packed` và `packing_done_at`
    (trạm 5 nhận bao nhiêu). Không có chúng thì màn hình phải đoán, mà đoán sai
    là hiện nút cho việc đã làm rồi.
    """
    rows = db.execute(text(AT_STATION_SQL), {"station": station}).mappings()
    return [dict(r) for r in rows]


def queue_counts(db: Session) -> dict[int, int]:
    """Đếm hàng chờ cả sáu trạm bằng MỘT câu, cộng sẵn nhóm chờ bàn giao vào trạm 0.

    Dựng từ chính `QUEUE_SQL` nên con số luôn khớp danh sách — xem đầu file.
    """
    phan = [f"SELECT {n} AS step_no, count(*) AS n FROM ({sql}) q"
            for n, sql in sorted(QUEUE_SQL.items())]
    phan.append(f"SELECT 0 AS step_no, ({CHO_BAN_GIAO_SQL}) AS n")
    rows = db.execute(text(" UNION ALL ".join(phan))).mappings().all()

    dem = dict.fromkeys(STEP_NAMES, 0)
    for r in rows:
        dem[r["step_no"]] += r["n"]          # trạm 0 cộng dồn hai nhánh
    return dem


def line_rows_of_rounds(db: Session, round_ids: list[uuid.UUID]) -> dict[uuid.UUID, list[dict]]:
    """Năng suất từng chuyền, cho NHIỀU vòng một lần. Vòng chưa có chuyền → thiếu khoá."""
    if not round_ids:
        return {}
    rows = db.execute(
        text(
            """
            SELECT t.round_id, l.code AS line_code, t.wait_sec, t.run_sec
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
