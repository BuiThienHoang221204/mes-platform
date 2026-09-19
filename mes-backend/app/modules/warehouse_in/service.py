"""Luật của trạm 5 — nơi MO đóng lại HOẶC chạy tiếp. Phòng Kho nhập.

    CompleteOutcome                        COMPLETED | ROUND_OPENED + số còn thiếu
    complete(db, code, actor_id)           nhận hàng về kho

Đây là chỗ DUY NHẤT quyết định MO xong hay chưa, nên cũng phải gọi `round_service`.
Tiến độ tính theo SL ĐÃ ĐÓNG THÙNG của vòng, không theo SL đạt (§8).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.common import clock
from app.common.errors import DomainError
from app.common.event_log import repository as event_repo
from app.common.uow import transactional
from app.common.vocab.action_codes import Act
from app.common.vocab.enums import RETURN_TO_BANCHO, STEP_NAMES
from app.common.vocab.error_codes import Err
from app.common.vocab.state_names import State
from app.modules.packing import repository as packing_repo
from app.modules.round import repository as round_repo
from app.modules.round import service as round_service
from app.modules.warehouse_in import repository as warehouse_in_repo
from app.modules.warehouse_in.schemas import Outcome
from app.common.event_bus import mark_affected


@dataclass(frozen=True)
class CompleteOutcome:
    """Hai kết cục: COMPLETED (đủ SL) hoặc ROUND_OPENED (thiếu, đã mở vòng mới)."""

    outcome: Outcome      # kiểu khai chung với schema — xem `schemas.Outcome`
    qty_done: int
    qty_remain: int
    new_round_no: int | None


@transactional
def complete(db: Session, *, code: str, actor_id: uuid.UUID) -> CompleteOutcome:
    """BRD §8: tổng = qtyDone + SL đã đóng thùng của vòng này.

    Đủ  → COMPLETED.
    Thiếu → tự động về BÀN TEAM LEADER vòng mới. Không về Kho: máy đã setup đúng, hàng đã
    qua QC, chỉ là chưa làm đủ số.

    **Không nhận số đếm từ client.** Hàng đã vào thùng bao nhiêu thì kho nhận bấy
    nhiêu — đó cũng đúng là công thức §8 vốn dĩ đang dùng. Tham số `qty_received` cũ
    được ghi xuống CSDL nhưng **không ai đọc**: gõ 0 hay 999.999 đều ra cùng kết cục,
    vì tiến độ lấy từ `v_mo_progress.qty_done = SUM(packing.qty_packed)`.
    """
    mo, rnd = round_service.lock_round(db, code)
    if round_repo.get_step(db, rnd.id, 5) is None:
        raise DomainError("Nhập kho chưa quét nhận lệnh này", code=Err.NO_WAREHOUSE_IN_ACCEPT)
    if warehouse_in_repo.get_warehouse_in(db, rnd.id) is not None:
        raise DomainError("Vòng này đã nhập kho rồi", code=Err.WAREHOUSE_IN_DONE)

    pack = packing_repo.get_packing(db, rnd.id)
    if pack is None or pack.completed_at is None:
        raise DomainError("Chưa kết thúc đóng thùng", code=Err.NO_PACKING)

    warehouse_in_repo.save_warehouse_in(db, rnd.id, qty_received=pack.qty_packed or 0,
                                   counted_at=clock.db_now(db), by=actor_id)
    step5 = round_repo.get_step(db, rnd.id, 5)
    if step5 is not None:
        round_repo.close_step(db, step5, actor_id)
    db.flush()

    p = round_service.progress(db, mo.id)
    if p.qty_done >= p.quantity:
        round_service.close_round_completed(db, mo=mo, current=rnd, actor_id=actor_id)
        mark_affected(5)
        return CompleteOutcome("COMPLETED", p.qty_done, 0, None)

    nxt = round_service.open_next_round(
        db, mo=mo, current=rnd, returned_to_step=RETURN_TO_BANCHO,
        reason=f"Còn {p.qty_remain} chưa đóng thùng — về Bàn team leader làm tiếp",
        actor_id=actor_id,
    )
    event_repo.log(db, mo_id=mo.id, round_id=rnd.id, step_no=5, action=Act.MO_PARTIAL,
             from_state=STEP_NAMES[5], to_state=State.NEW_ROUND_AT_WAITING_DESK,
             reason=f"cộng dồn {p.qty_done}/{p.quantity}", actor_id=actor_id)
    # ROUND_OPENED: station 5 (atStation), station 3 (queue vòng mới)
    mark_affected(5, 3)
    return CompleteOutcome("ROUND_OPENED", p.qty_done, p.qty_remain, nxt.round_no)
