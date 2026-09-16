"""Luật đóng thùng — chạy SONG SONG với sản xuất. Phòng Sản xuất, trong trạm 4.

    packing_start(db, rnd, actor_id)       cần ít nhất một chuyền đã chạy
    packing_finish(db, rnd, qty_packed…)   ghi SL đã đóng

`qty_packed` mới là con số đẩy tiến độ MO, không phải `qty_ok`. Trigger
`packing_within_ok` ở DB chặn đóng vượt SL đạt và chặn kết thúc khi chưa chốt sổ SX.
"""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.common import clock
from app.common.errors import DomainError, Invalid
from app.common.event_log import repository as event_repo
from app.common.uow import transactional
from app.common.vocab.action_codes import Act
from app.common.vocab.enums import SegmentKind
from app.common.vocab.error_codes import Err
from app.common.vocab.state_names import State
from app.modules.packing import repository as packing_repo
from app.modules.packing.models import Packing
from app.modules.production import repository as production_repo
from app.modules.round import service as round_service


@transactional
def packing_start(db: Session, *, code: str, actor_id: uuid.UUID) -> Packing:
    """Mở sổ đóng thùng. Cần ít nhất một chuyền đã vào Đang lắp ráp (§7b)."""
    _, rnd = round_service.lock_round(db, code)
    if packing_repo.get_packing(db, rnd.id) is not None:
        raise DomainError("Vòng này đã bắt đầu đóng thùng rồi", code=Err.PACK_STARTED)
    if not any(s.kind == SegmentKind.RUN for s in production_repo.segments_of(db, rnd.id)):
        raise DomainError("Chưa chuyền nào chạy — chưa đóng thùng được (§7b)", code=Err.NO_RUN)

    row = packing_repo.save_packing(db, rnd.id, actor_id)
    db.flush()
    event_repo.log(db, mo_id=rnd.mo_id, round_id=rnd.id, step_no=4, action=Act.PACK_START,
             to_state=State.PACKING, actor_id=actor_id)
    return row


@transactional
def packing_finish(db: Session, *, code: str, qty_packed: int, note_text: str | None,
                   actor_id: uuid.UUID) -> Packing:
    """Kết thúc đóng thùng. Trigger `packing_within_ok` chặn vượt SL đạt và chặn
    kết thúc khi chưa chốt sổ SX."""
    _, rnd = round_service.lock_round(db, code)
    row = packing_repo.get_packing(db, rnd.id)
    if row is None:
        raise DomainError("Chưa bắt đầu đóng thùng", code=Err.NO_PACK)
    if row.completed_at is not None:
        raise DomainError("Đã kết thúc đóng thùng rồi", code=Err.PACK_DONE)
    if qty_packed <= 0:
        raise Invalid("SL đã đóng thùng phải lớn hơn 0")

    row.qty_packed = qty_packed
    row.note_text = note_text
    row.completed_at = clock.db_now(db)
    row.completed_by = actor_id
    db.flush()
    event_repo.log(db, mo_id=rnd.mo_id, round_id=rnd.id, step_no=4, action=Act.PACK_COMPLETE,
             to_state=State.FINISHED, reason=f"đóng {qty_packed} — {note_text or ''}",
             actor_id=actor_id)
    return row
