"""Trạm 2 — QC. Phòng QC.

    POST /qc/{code}                    ghi kết quả PASS / FAIL

FAIL trả MO về KHO (0) và mở vòng mới, KHÔNG về Bàn team leader (3): setup sai mà cho về
Bàn team leader thì MO nhảy qua luôn Setup và QC, hàng lỗi đi thẳng vào chuyền (§5).
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter

from app.common.deps import ActorDep, DbDep
from app.common.vocab.enums import QcVerdict
from app.modules.qc import service as qc_service
from app.modules.qc.schemas import QcDecideIn, QcOut

router = APIRouter(tags=["qc"])


@router.post("/qc/{code}", response_model=QcOut)
def qc(code: str, body: QcDecideIn, db: DbDep, actor: ActorDep) -> QcOut:
    """Ghi kết quả kiểm: PASS → đi tiếp Bàn team leader, FAIL → về KHO và mở vòng mới.
    FAIL bắt buộc có lý do."""
    actor.require_step(2)
    out = qc_service.qc_decide(
        db, code=code, result=QcVerdict(body.result),
        reason_code_id=body.reason_code_id, reason_text=body.reason_text,
        actor_id=uuid.UUID(actor.user_id),
    )
    msg = ("QC đạt — chuyển Bàn team leader" if out.result == QcVerdict.PASS
           else f"QC không đạt — {code} về Kho, mở vòng {out.new_round_no}")
    return QcOut(result=out.result, new_round_no=out.new_round_no, message=msg)
