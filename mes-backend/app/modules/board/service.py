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

from datetime import date, datetime

from sqlalchemy.orm import Session

from app.common.clock import local_dt
from app.common.config import settings
from app.common.deps import PAGE_SIZE
from app.common.errors import NotFound
from app.common.event_log import repository as event_repo
from app.common.vocab.enums import STEP_NAMES, MoStatus
from app.modules.board import repository as board_repo
from app.modules.catalog import repository as catalog_repo
from app.modules.mo import repository as mo_repo
from app.modules.packing import repository as packing_repo
from app.modules.production import repository as production_repo
from app.modules.round import repository as round_repo


def running_board(db: Session, *, limit: int, offset: int = 0) -> dict:
    """MỘT TRANG bảng lệnh đang chạy — mỗi vòng đang mở một dòng, kèm KPI thời gian."""
    result = {"items": board_repo.running_rows(db, limit=limit, offset=offset),
              "total": board_repo.count_running(db)}
    for item in result["items"]:
        for key in ("production_closed_at", "packing_done_at", "handed_over_at"):
            v = item.get(key)
            if isinstance(v, datetime):
                item[key] = local_dt(v)
    return result

def queue(db: Session, station: int, *, limit: int, offset: int = 0) -> dict:
    """MỘT TRANG hàng đợi: vòng đang mở, đã qua bước trước, chưa nhận bước này."""
    return {"items": board_repo.queue_rows(db, station, limit=limit, offset=offset),
            "total": board_repo.count_queue(db, station)}

OVERVIEW_SCAN = 200
"""Số vòng đang chạy soi tới để dựng cảnh báo.

Năm con số ở đầu màn là `COUNT(*)` nên luôn đúng với toàn xưởng. Riêng cảnh báo
phải mở từng dòng ra xem, nên có trần. Xưởng 14 chuyền không bao giờ có 200 vòng
mở cùng lúc; nếu có thì `alerts_total` nói rõ còn bao nhiêu chưa soi.
"""

WAREHOUSE_OUT = 0


def overview(db: Session, *, alert_limit: int = 50) -> dict:
    """Gom cả màn Tổng quan vào MỘT lời gọi.

    Thứ tự cảnh báo là thứ tự KHẨN: chuyền đang dừng (xưởng đứng im) → quá giờ →
    QC trả về → đang làm bù. Một lệnh vừa quá giờ vừa ở vòng 2+ chỉ hiện MỘT lần,
    ở mục nặng hơn — hiện hai lần là người đọc tưởng có hai việc phải xử.
    """
    rows = board_repo.running_rows(db, limit=OVERVIEW_SCAN, offset=0)
    kho_queue = board_repo.queue_rows(db, WAREHOUSE_OUT, limit=OVERVIEW_SCAN, offset=0)

    busy: set[str] = set()
    held_alerts: list[dict] = []
    late_alerts: list[dict] = []
    re_round_rows: list[dict] = []
    lines_held = 0

    for r in rows:
        held_here: list[str] = []
        for ln in r.get("lines") or []:
            if ln.get("current_kind"):
                busy.add(ln["line_code"])
            if ln.get("current_kind") == "WAIT" and ln.get("hold_reason"):
                held_here.append(ln["line_code"])
        lines_held += len(held_here)

        if held_here:
            held_alerts.append({
                "kind": "HOLD", "code": r["code"], "round_no": r["round_no"],
                "lines": held_here,
                "reason": next(
                    (ln.get("hold_reason") for ln in (r.get("lines") or [])
                     if ln.get("hold_reason")), None),
            })
        if r.get("on_time") is False:
            late_alerts.append({
                "kind": "LATE", "code": r["code"], "round_no": r["round_no"],
                "late_sec": r.get("late_sec"), "required_sec": r.get("required_sec"),
                "target_qty": r.get("target_qty"),
            })
        if r["round_no"] > 1:
            re_round_rows.append(r)

    rework_rows = [q for q in kho_queue if q["round_no"] > 1]
    rework_alerts = [
        {"kind": "REWORK", "code": q["code"], "round_no": q["round_no"]}
        for q in rework_rows
    ]

    late_codes = {a["code"] for a in late_alerts}
    re_round_alerts = [
        {"kind": "RE_ROUND", "code": r["code"], "round_no": r["round_no"],
         "target_qty": r.get("target_qty"), "quantity": r.get("quantity")}
        for r in re_round_rows if r["code"] not in late_codes
    ]

    alerts = held_alerts + late_alerts + rework_alerts + re_round_alerts

    return {
        "running_rounds": board_repo.count_running(db),
        "lines_total": len(catalog_repo.list_lines(db)),
        "lines_busy": len(busy),
        "lines_held": lines_held,
        "rework": len(rework_rows),
        "re_round": len(re_round_rows),
        "completed": mo_repo.count_mos(db, status=MoStatus.COMPLETED),
        "alerts": alerts[:alert_limit],
        "alerts_total": len(alerts),
    }


def at_station(db: Session, station: int, *, limit: int, offset: int = 0) -> dict:
    """MỘT TRANG lệnh đang nằm trong tay trạm — đã nhận, chưa trạm sau lấy đi."""
    return {"items": board_repo.at_station_rows(db, station, limit=limit, offset=offset),
            "total": board_repo.count_at_station(db, station)}

def station_counts(db: Session, *, date_from: date | None = None,
                   date_to: date | None = None) -> tuple[dict[int, int], dict[int, int]]:
    """Hai con số mỗi trạm: chờ nhận và đang giữ.

    Con số chờ nhận và danh sách của `queue` dựng từ cùng một nguồn SQL nên không
    thể lệch nhau — xem `repository.QUEUE_SQL`.
    """
    return board_repo.queue_counts(db, date_from=date_from, date_to=date_to)

def _hourly_out(h) -> dict:
    """BA số mỗi khung giờ (§7.2b). `headcount`/`target_qty` NULL được — dòng ghi
    trước migration 0006 không có chúng."""
    return {
        "work_date": h.work_date, "slot_hour": h.slot_hour,
        "headcount": h.headcount, "target_qty": h.target_qty,
        "qty": h.qty, "note": h.note, "recorded_at": local_dt(h.recorded_at),
    }

def _box_out(b) -> dict:
    """Sổ thùng theo giờ (§7b.2). `pcs_per_box` ĐÓNG DẤU vào từng dòng, không đọc
    sang `manufacturing_order` — quy cách sửa một lần là mọi dòng cũ quy ra khác."""
    return {
        "work_date": b.work_date, "slot_hour": b.slot_hour,
        "boxes": b.boxes, "pcs_per_box": b.pcs_per_box,
        "note": b.note, "recorded_at": local_dt(b.recorded_at),
    }

def _round_of(db: Session, mo_code: str, round_no: int):
    """Vòng thứ `round_no` của một MO, hoặc ném lỗi."""
    mo = mo_repo.get_mo(db, mo_code)
    rnd = next((r for r in round_repo.rounds_of(db, mo.id) if r.round_no == round_no), None)
    if rnd is None:
        raise NotFound(f"{mo_code} không có vòng {round_no}")
    return rnd

def round_hourly(db: Session, mo_code: str, round_no: int, *,
                 limit: int, offset: int) -> dict:
    """MỘT TRANG sản lượng giờ của một vòng — nút Xem thêm của màn truy cứu gọi vào đây.

    Tách khỏi `trace` cùng lý lẽ với nhật ký: `steps` tối đa 6, `lines` tối đa 14,
    số vòng hiếm khi quá 5 — ba thứ đó có trần tự nhiên. Chỉ sổ giờ và sổ thùng là
    KHÔNG có trần, nên chúng mới là phần làm cây truy cứu phình theo thời gian.
    """
    rnd = _round_of(db, mo_code, round_no)
    return {
        "items": [_hourly_out(h) for h in
                  production_repo.hourly_page(db, rnd.id, limit=limit, offset=offset)],
        "total": production_repo.count_hourly(db, rnd.id),
    }

def round_boxes(db: Session, mo_code: str, round_no: int, *,
                limit: int, offset: int) -> dict:
    """MỘT TRANG sổ thùng theo giờ của một vòng."""
    rnd = _round_of(db, mo_code, round_no)
    return {
        "items": [_box_out(b) for b in
                  packing_repo.packing_hourly_page(db, rnd.id, limit=limit, offset=offset)],
        "total": packing_repo.count_packing_hourly(db, rnd.id),
    }

def trace(db: Session, mo_code: str) -> dict:
    """Truy cứu một MO: mọi vòng, mọi bước, năng suất từng chuyền, sản lượng giờ."""
    mo = mo_repo.get_mo(db, mo_code)
    rounds = round_repo.rounds_of(db, mo.id)
    ids = [r.id for r in rounds]

    steps = round_repo.steps_of_rounds(db, ids)
    lines = board_repo.line_rows_of_rounds(db, ids)
    hourly = production_repo.hourly_of_rounds(db, ids)
    production = production_repo.production_of_rounds(db, ids)
    packing = packing_repo.packing_of_rounds(db, ids)
    box_hourly = packing_repo.packing_hourly_of_rounds(db, ids)

    user_names = round_repo.names_of_users(
        db,
        [
            x
            for st in steps.values()
            for s in st
            for x in (s.accepted_by, s.closed_by)
            if x is not None
        ],
    )

    return {
        "code": mo.code,
        "product_name": mo.product_name,
        "quantity": mo.quantity,
        "pcs_per_box": mo.pcs_per_box,
        "status": mo.status,
        "progress": board_repo.mo_progress(db, mo.id),
        "step_totals": board_repo.step_totals(db, mo.id),
        "rounds": [
            {
                "round_no": rnd.round_no,
                "started_from": rnd.returned_to_step,   # 0 Kho · 3 Bàn team leader — GHI, không suy
                "opened_at": local_dt(rnd.opened_at),
                "closed_at": local_dt(rnd.closed_at),
                "target_qty": rnd.target_qty,
                "required_sec": rnd.required_sec,
                "return_reason_text": rnd.return_reason_text,
                "steps": [
                    {
                        "step_no": s.step_no,
                        "name": STEP_NAMES[s.step_no],
                        "accepted_at": local_dt(s.accepted_at),
                        "accepted_by": user_names.get(s.accepted_by),
                        "closed_at": local_dt(s.closed_at),
                        "closed_by": user_names.get(s.closed_by) if s.closed_by else None,
                    }
                    for s in steps.get(rnd.id, [])
                ],
                "lines": lines.get(rnd.id, []),
                "hourly": [_hourly_out(h) for h in hourly.get(rnd.id, [])[:PAGE_SIZE]],
                "hourly_total": len(hourly.get(rnd.id, [])),
                "hourly_qty_total": sum(h.qty for h in hourly.get(rnd.id, [])),
                "hourly_target_total": sum(h.target_qty or 0 for h in hourly.get(rnd.id, [])),
                "packing_hourly": [_box_out(b) for b in box_hourly.get(rnd.id, [])[:PAGE_SIZE]],
                "packing_hourly_total": len(box_hourly.get(rnd.id, [])),
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
        "events": events_page(db, mo.id, limit=EVENT_PAGE, offset=0),
        "events_total": event_repo.count_events(db, mo.id),
    }

EVENT_PAGE = PAGE_SIZE
"""Số dòng nhật ký mỗi trang. FE và BE phải nói cùng một con số, nên nó ở đây."""

def events_page(db: Session, mo_id, *, limit: int, offset: int) -> list[dict]:
    """Một trang nhật ký đã dịch sang hình dạng màn hình cần."""
    return [
        {
            "at": local_dt(e.occurred_at), "action": e.action, "step_no": e.step_no,
            "from": e.from_state, "to": e.to_state, "reason": e.reason_text,
        }
        for e in event_repo.events_of(db, mo_id, limit=limit, offset=offset)
    ]

def events(db: Session, mo_code: str, *, limit: int, offset: int) -> dict:
    """Một trang nhật ký của MO, kèm tổng số dòng để biết còn trang sau không."""
    mo = mo_repo.get_mo(db, mo_code)
    return {
        "items": events_page(db, mo.id, limit=limit, offset=offset),
        "total": event_repo.count_events(db, mo.id),
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
    result = {}
    for f in fields:
        v = getattr(row, f)
        result[f] = local_dt(v) if isinstance(v, datetime) else v
    return result
