"""Nhận một bước — thao tác chung của cả sáu trạm.

    guard_can_accept(db, rnd, step_no)     chặn nhảy bước, báo RÕ lý do
    accept(db, rnd, step_no, actor_id)     đóng bước trước + mở bước này

Không có nút Hoàn thành: bước N đóng khi bước N+1 quét, `closed_by` là người quét sau (§9).
LƯU Ý: `guard_can_accept` đọc sang 4 module trạm → phụ thuộc HAI CHIỀU, nên chuyển sang `scan/`.
"""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.common.errors import DomainError
from app.common.event_log import repository as event_repo
from app.common.vocab.action_codes import step_accept
from app.common.vocab.enums import STEP_NAMES
from app.common.vocab.error_codes import Err
from app.modules.packing import repository as packing_repo
from app.modules.production import repository as production_repo
from app.modules.qc import repository as qc_repo
from app.modules.round import repository as round_repo
from app.modules.round.models import MoRound, MoStep
from app.modules.warehouse_out import repository as warehouse_out_repo


def guard_can_accept(db: Session, rnd: MoRound, step_no: int) -> None:
    """Chặn nhảy bước. Báo RÕ LÝ DO, không im lặng (BRD §1b.3)."""
    if round_repo.get_step(db, rnd.id, step_no) is not None:
        raise DomainError(f"MO đã nhận ở trạm {STEP_NAMES[step_no]} rồi", code=Err.STEP_DONE)

    if step_no == 1:
        # §3.2 — chưa bàn giao thì Setup không nhận được
        if warehouse_out_repo.get_warehouse_out(db, rnd.id) is None:
            raise DomainError("Chưa bàn giao — Setup không nhận được", code=Err.NO_HANDOVER)
    elif step_no == 3:
        qc = qc_repo.get_qc(db, rnd.id)
        if qc is None:
            raise DomainError("Chưa có kết quả QC", code=Err.NO_QC)
        if qc.result != "PASS":
            raise DomainError("QC không đạt — MO đã quay về Kho", code=Err.QC_FAILED)
    elif step_no == 5:
        prod = production_repo.get_production(db, rnd.id)
        pack = packing_repo.get_packing(db, rnd.id)
        if prod is None:
            raise DomainError("Chưa chốt sổ Sản xuất", code=Err.NO_PRODUCTION)
        if pack is None or pack.completed_at is None:
            raise DomainError("Chưa kết thúc đóng thùng", code=Err.NO_PACKING)
    elif step_no not in (0, 2, 4):
        raise DomainError(f"Trạm {step_no} không hợp lệ")

    # Các bước 1..5 đòi bước liền trước đã được nhận. Riêng bước 3 của vòng quay
    # về Bàn team leader được mở sẵn nên không bao giờ đi qua đây.
    if step_no >= 1:
        prev = round_repo.get_step(db, rnd.id, step_no - 1)
        if prev is None:
            raise DomainError(
                f"Chưa qua trạm {STEP_NAMES[step_no - 1]} — không nhảy bước được",
                code=Err.SKIP_STEP,
            )


def accept(db: Session, *, rnd: MoRound, step_no: int, actor_id: uuid.UUID) -> MoStep:
    """Nhận bước: đóng bước trước, mở bước này, ghi nhật ký — trong MỘT transaction."""
    guard_can_accept(db, rnd, step_no)

    # Bước trước tự đóng, và ghi lại AI đóng nó — cột đáng giá nhất để truy cứu
    if step_no >= 1:
        prev = round_repo.get_step(db, rnd.id, step_no - 1)
        if prev is not None:
            round_repo.close_step(db, prev, actor_id)

    step = round_repo.open_step(db, rnd.id, step_no, actor_id)
    event_repo.log(db, mo_id=rnd.mo_id, round_id=rnd.id, step_no=step_no,
             action=step_accept(step_no),
             from_state=STEP_NAMES.get(step_no - 1, ""), to_state=STEP_NAMES[step_no],
             actor_id=actor_id)
    return step
