"""Luật của trạm 0 — Kho xuất bàn giao. Phòng Kho xuất.

    handover(db, rnd, actor_id)            ghi một dòng vào sổ `warehouse_out`

Hai điều kiện: Kho phải đã quét nhận lệnh, và chưa bàn giao lần nào. **Có dòng
nghĩa là đã bàn giao** — chưa có dòng thì Setup không quét nhận được (§3.2).
"""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.common.errors import DomainError
from app.common.event_log import repository as event_repo
from app.common.uow import transactional
from app.common.vocab.action_codes import Act
from app.common.vocab.enums import STEP_NAMES
from app.common.vocab.error_codes import Err
from app.modules.round import repository as round_repo
from app.modules.round import service as round_service
from app.modules.warehouse_out import repository as warehouse_out_repo
from app.modules.warehouse_out.models import WarehouseOut


@transactional
def handover(db: Session, *, code: str, actor_id: uuid.UUID) -> WarehouseOut:
    """Bàn giao xuống xưởng. Từ BRD v2.18 đây là thao tác DUY NHẤT của Kho —
    không còn bước In phiếu."""
    _, rnd = round_service.lock_round(db, code)
    if round_repo.get_step(db, rnd.id, 0) is None:
        raise DomainError("Kho chưa quét nhận lệnh này", code=Err.NO_WAREHOUSE_OUT_ACCEPT)
    if warehouse_out_repo.get_warehouse_out(db, rnd.id) is not None:
        raise DomainError("Lệnh này đã bàn giao rồi", code=Err.HANDED_OVER)

    row = warehouse_out_repo.save_handover(db, rnd.id, actor_id)
    db.flush()
    event_repo.log(db, mo_id=rnd.mo_id, round_id=rnd.id, step_no=0, action=Act.KHO_HANDOVER,
             from_state=STEP_NAMES[0], to_state=STEP_NAMES[1], actor_id=actor_id)
    return row


@transactional
def handover_batch(db: Session, *, codes: list[str], actor_id: uuid.UUID) -> int:
    """Bàn giao cả lô 10–100 lệnh (§7A) — MỘT đơn vị công việc.

    Một mã hỏng thì cả lô không lệnh nào được giao. `handover` bên dưới cũng có
    `@transactional` nhưng nó NHẬP VÀO giao dịch này chứ không mở cái mới — đó là
    propagation REQUIRED. Không có nó thì mã thứ 7 hỏng mà sáu mã đầu đã giao rồi.
    """
    for code in codes:
        handover(db, code=code, actor_id=actor_id)
    return len(codes)
