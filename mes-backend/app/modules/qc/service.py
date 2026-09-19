"""Luật của trạm 2 — QC. Phòng QC.

    QcOutcome                              kết quả + số vòng mới nếu FAIL
    qc_decide(db, mo, rnd, result…)        ghi PASS / FAIL

FAIL mở vòng mới về KHO (0) trong cùng transaction — nên file này gọi `round_service`.
Không về Bàn team leader (3): MO sẽ nhảy qua Setup và QC, hàng lỗi đi thẳng vào chuyền (§5).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.common.errors import DomainError
from app.common.event_log import repository as event_repo
from app.common.uow import transactional
from app.common.vocab.action_codes import Act
from app.common.vocab.enums import RETURN_TO_KHO, STEP_NAMES, QcVerdict
from app.common.vocab.error_codes import Err
from app.common.vocab.state_names import State
from app.modules.qc import repository as qc_repo
from app.modules.round import repository as round_repo
from app.modules.round import service as round_service
from app.common.event_bus import mark_affected


@dataclass(frozen=True)
class QcOutcome:
    """Kết quả QC. `new_round_no` chỉ có giá trị khi FAIL — vòng mới về Kho."""
    result: QcVerdict
    new_round_no: int | None   # có giá trị khi FAIL → mở vòng mới về Kho


@transactional
def qc_decide(db: Session, *, code: str, result: QcVerdict,
              reason_code_id: int | None, reason_text: str | None,
              actor_id: uuid.UUID) -> QcOutcome:
    """Ghi kết quả kiểm. PASS thì xong; FAIL thì đóng bước 2 và mở vòng mới về KHO."""
    mo, rnd = round_service.lock_round(db, code)
    if round_repo.get_step(db, rnd.id, 2) is None:
        raise DomainError("QC chưa quét nhận lệnh này", code=Err.NO_QC_ACCEPT)
    if qc_repo.get_qc(db, rnd.id) is not None:
        raise DomainError("Vòng này đã có kết quả QC rồi", code=Err.QC_DONE)

    qc_repo.save_qc(db, rnd.id, result=result, by=actor_id,
                    reason_code_id=reason_code_id, reason_text=reason_text)
    db.flush()  # CHECK qc_fail_needs_reason nổ ở đây nếu FAIL mà không có lý do

    if result == QcVerdict.PASS:
        event_repo.log(db, mo_id=mo.id, round_id=rnd.id, step_no=2, action=Act.QC_PASS,
                 to_state=State.AWAITING_WAITING_DESK, actor_id=actor_id)
        # PASS: station 2 (atStation), station 3 (queue hiện lệnh này)
        mark_affected(2, 3)
        return QcOutcome(result, None)

    # FAIL → về KHO, không về Bàn team leader. Cho về Bàn team leader thì MO nhảy qua luôn Setup
    # và QC — hàng lỗi setup đi thẳng vào chuyền mà không ai sửa máy (BRD §5).
    step2 = round_repo.get_step(db, rnd.id, 2)
    if step2 is not None:
        round_repo.close_step(db, step2, actor_id)
    why = reason_text or "QC FAIL"
    nxt = round_service.open_next_round(
        db, mo=mo, current=rnd, returned_to_step=RETURN_TO_KHO,
        reason=f"QC FAIL: {why}", actor_id=actor_id,
    )
    event_repo.log(db, mo_id=mo.id, round_id=rnd.id, step_no=2, action=Act.QC_FAIL,
             from_state=STEP_NAMES[2], to_state=State.NEW_ROUND_AT_WAREHOUSE,
             reason=why, actor_id=actor_id)
    # FAIL: station 2 (atStation), station 0 (queue vòng mới)
    mark_affected(2, 0)
    return QcOutcome(result, nxt.round_no)
