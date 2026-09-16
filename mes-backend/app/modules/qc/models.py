"""Bảng `qc_result` — sổ trạm 2 (QC). 1-1 với vòng.

FAIL trả MO về KHO (0), KHÔNG phải Bàn team leader (3) — về Bàn team leader thì MO nhảy qua Setup và
QC, hàng lỗi đi thẳng vào chuyền (§5). FAIL bắt buộc có lý do, CHECK ở DB canh.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.common.base import Base, qc_verdict_enum
from app.common.vocab.enums import QcVerdict


class QcResult(Base):
    __tablename__ = "qc_result"
    round_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("mo_round.id", ondelete="CASCADE"), primary_key=True)
    result: Mapped[QcVerdict] = mapped_column(qc_verdict_enum, nullable=False)
    checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                 nullable=False, server_default=func.now())
    checked_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("app_user.id"), nullable=False)
    reason_code_id: Mapped[int | None] = mapped_column(ForeignKey("reason_code.id"))
    reason_text: Mapped[str | None] = mapped_column(Text)
