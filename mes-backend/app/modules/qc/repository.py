"""Truy vấn sổ trạm 2 — `qc_result`.

    get_qc(db, round_id)                   None = chưa kiểm

Một vòng chỉ có MỘT kết quả QC (PK là `round_id`). Muốn kiểm lại thì phải mở vòng
mới — đó chính là đường QC FAIL về Kho.
"""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.common.vocab.enums import QcVerdict
from app.modules.qc.models import QcResult


def save_qc(db: Session, round_id: uuid.UUID, *, result: QcVerdict, by: uuid.UUID,
            reason_code_id: int | None, reason_text: str | None) -> QcResult:
    """Ghi kết quả kiểm. `CHECK qc_fail_needs_reason` nổ lúc flush nếu FAIL mà thiếu lý do."""
    row = QcResult(round_id=round_id, result=result, checked_by=by,
                   reason_code_id=reason_code_id, reason_text=reason_text)
    db.add(row)
    return row


def get_qc(db: Session, round_id: uuid.UUID) -> QcResult | None:
    """Kết quả QC của một vòng. None = chưa kiểm; một vòng chỉ có MỘT kết quả."""
    return db.get(QcResult, round_id)
