"""Đọc view cho các màn hình. CHỈ ĐỌC, không transaction.

    running_board(db)                      bảng lệnh đang chạy + KPI
    queue(db, station)                     hàng chờ của một trạm
    station_counts(db)                     badge số lệnh từng trạm
    trace(db, mo_code)                     cây truy vết đầy đủ một MO

Mọi câu SQL nằm ở `repository.py`; file này chỉ ghép dữ liệu thành hình dạng mà
màn hình cần.

`trace` đọc TRƯỚC rồi ghép SAU: lấy hết `round_id` một lượt, hỏi mỗi bảng đúng một
câu, rồi mới dựng cây. Trước đây nó hỏi từng vòng một nên MO bốn vòng tốn 25 câu
SQL; nay còn 10 câu bất kể bao nhiêu vòng.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.common.event_log import repository as event_repo
from app.common.vocab.enums import STEP_NAMES
from app.modules.board import repository as board_repo
from app.modules.mo import repository as mo_repo
from app.modules.packing import repository as packing_repo
from app.modules.production import repository as production_repo
from app.modules.round import repository as round_repo


def running_board(db: Session) -> list[dict]:
    """Bảng lệnh đang chạy — mỗi vòng đang mở một dòng, kèm KPI thời gian."""
    return board_repo.running_rows(db)


def queue(db: Session, station: int) -> list[dict]:
    """Hàng đợi của một trạm: vòng đang mở, đã qua bước trước, chưa nhận bước này."""
    return board_repo.queue_rows(db, station)


def at_station(db: Session, station: int) -> list[dict]:
    """Lệnh đang nằm trong tay một trạm — đã nhận, chưa trạm sau lấy đi."""
    return board_repo.at_station_rows(db, station)


def station_counts(db: Session) -> dict[int, int]:
    """Con số trên thanh trạm — MỘT câu SQL cho cả sáu trạm.

    Riêng Kho đếm CẢ HAI nhóm: lệnh chưa ai nhận, và lệnh đã nhận nhưng chưa bàn
    giao — hàng vẫn còn ở kho, vẫn cần người làm tiếp. Chỉ đếm nhóm đầu thì badge
    hiện 0 trong khi kho còn hàng nằm đó.

    Con số ở đây và danh sách của `queue` dựng từ cùng một nguồn SQL nên không thể
    lệch nhau — xem `repository.QUEUE_SQL`.
    """
    return board_repo.queue_counts(db)


def trace(db: Session, mo_code: str) -> dict:
    """Truy cứu một MO: mọi vòng, mọi bước, năng suất từng chuyền, sản lượng giờ."""
    mo = mo_repo.get_mo(db, mo_code)
    rounds = round_repo.rounds_of(db, mo.id)
    ids = [r.id for r in rounds]

    # Năm câu cho MỌI vòng, thay vì năm câu MỖI vòng.
    steps = round_repo.steps_of_rounds(db, ids)
    lines = board_repo.line_rows_of_rounds(db, ids)
    hourly = production_repo.hourly_of_rounds(db, ids)
    production = production_repo.production_of_rounds(db, ids)
    packing = packing_repo.packing_of_rounds(db, ids)
    box_hourly = packing_repo.packing_hourly_of_rounds(db, ids)

    return {
        "code": mo.code,
        "product_name": mo.product_name,
        "quantity": mo.quantity,
        # Màn Sản xuất cần quy cách để chia thùng lúc kết thúc đóng thùng, và nó
        # phải có TRƯỚC khi ghi thùng đầu tiên — không suy được từ `packing_hourly`.
        "pcs_per_box": mo.pcs_per_box,
        "status": mo.status,
        "progress": board_repo.mo_progress(db, mo.id),
        # Cộng dồn qua MỌI vòng — không chỉ vòng cuối
        "step_totals": board_repo.step_totals(db, mo.id),
        "rounds": [
            {
                "round_no": rnd.round_no,
                "started_from": rnd.returned_to_step,   # 0 Kho · 3 Bàn team leader — GHI, không suy
                "opened_at": rnd.opened_at,
                "closed_at": rnd.closed_at,
                "target_qty": rnd.target_qty,
                "required_sec": rnd.required_sec,
                "return_reason_text": rnd.return_reason_text,
                "steps": [
                    {
                        "step_no": s.step_no,
                        "name": STEP_NAMES[s.step_no],
                        "accepted_at": s.accepted_at,
                        "accepted_by": s.accepted_by,
                        "closed_at": s.closed_at,
                        "closed_by": s.closed_by,
                    }
                    for s in steps.get(rnd.id, [])
                ],
                "lines": lines.get(rnd.id, []),
                # BA số mỗi khung giờ (§7.2b). `headcount`/`target_qty` NULL được —
                # dòng ghi trước migration 0006 không có chúng.
                "hourly": [
                    {
                        "work_date": h.work_date, "slot_hour": h.slot_hour,
                        "headcount": h.headcount, "target_qty": h.target_qty,
                        "qty": h.qty, "note": h.note, "recorded_at": h.recorded_at,
                    }
                    for h in hourly.get(rnd.id, [])
                ],
                # Sổ thùng theo giờ + HÀNG LẺ (§7b.2). `le_pcs` suy ra, không lưu —
                # và nó KHÔNG phải `qty_short`: thiếu là chưa làm ra được, lẻ là làm
                # rồi chưa đủ một thùng.
                "packing_hourly": [
                    {
                        "work_date": b.work_date, "slot_hour": b.slot_hour,
                        "boxes": b.boxes, "pcs_per_box": b.pcs_per_box,
                        "note": b.note, "recorded_at": b.recorded_at,
                    }
                    for b in box_hourly.get(rnd.id, [])
                ],
                "box_summary": _box_summary(
                    box_hourly.get(rnd.id, []),
                    production.get(rnd.id),
                    hourly.get(rnd.id, []),
                ),
                "production": _row_or_none(production.get(rnd.id),
                                           ("qty_ok", "qty_ng", "qty_short",
                                            "ng_reason_text", "short_reason_text", "closed_at")),
                "packing": _row_or_none(packing.get(rnd.id),
                                        ("qty_packed", "note_text",
                                         "started_at", "completed_at")),
            }
            for rnd in rounds
        ],
        "events": [
            {
                "at": e.occurred_at, "action": e.action, "step_no": e.step_no,
                "from": e.from_state, "to": e.to_state, "reason": e.reason_text,
            }
            for e in event_repo.events_of(db, mo.id)
        ],
    }


def _box_summary(boxes, prod, hours) -> dict:
    """Ba con số của đóng thùng trong một vòng.

    `made_pcs` lấy `qty_ok` khi đã chốt sổ, chưa thì tạm Σ sản lượng giờ — y hệt
    `packing/hourly_service._made_pcs`. Mục tiêu vòng là số PHẢI làm, không phải
    số ĐÃ làm, nên không lấy nó.
    """
    packed = sum(b.boxes * b.pcs_per_box for b in boxes)
    made = prod.qty_ok if prod is not None else sum(h.qty for h in hours)
    return {
        "boxes_total": sum(b.boxes for b in boxes),
        "packed_pcs": packed,
        "made_pcs": made,
        "le_pcs": max(0, made - packed),
    }


def _row_or_none(row, fields: tuple[str, ...]) -> dict | None:
    if row is None:
        return None
    return {f: getattr(row, f) for f in fields}
