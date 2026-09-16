"""Bảng `mo_round` và `mo_step` — TRỤC của cả hệ thống.

Hai bảng ở chung file vì bước không tồn tại ngoài vòng: `mo_step` khoá theo
`round_id`, và mở vòng mới là bắt đầu lại từ bước đầu.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, SmallInteger, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.base import Base, _uuid_pk

if TYPE_CHECKING:
    from app.modules.mo.models import ManufacturingOrder


class MoRound(Base):
    __tablename__ = "mo_round"
    id: Mapped[uuid.UUID] = _uuid_pk()
    mo_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("manufacturing_order.id"), nullable=False)
    round_no: Mapped[int] = mapped_column(Integer, nullable=False)

    # Đóng dấu lúc mở vòng, KHÔNG tính lại (BRD §6b.2, §7.3)
    target_qty: Mapped[int] = mapped_column(Integer, nullable=False)
    required_sec: Mapped[int] = mapped_column(Integer, nullable=False)

    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                nullable=False, server_default=func.now())
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # GHI lúc mở vòng, KHÔNG suy ra sau: 0 Kho (QC FAIL) · 3 Bàn team leader (thiếu SL).
    # Suy ngược từ danh sách bước thì hai đường này nhìn giống hệt nhau.
    returned_to_step: Mapped[int | None] = mapped_column(SmallInteger)
    return_reason_text: Mapped[str | None] = mapped_column(Text)

    mo: Mapped[ManufacturingOrder] = relationship(back_populates="rounds")
    steps: Mapped[list[MoStep]] = relationship(back_populates="round", order_by="MoStep.step_no")


class MoStep(Base):
    """Không có nút Hoàn thành: bước N đóng khi bước N+1 quét nhận."""

    __tablename__ = "mo_step"
    id: Mapped[uuid.UUID] = _uuid_pk()
    round_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("mo_round.id", ondelete="CASCADE"), nullable=False)
    step_no: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    accepted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                  nullable=False, server_default=func.now())
    accepted_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("app_user.id"), nullable=False)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Cột đáng giá nhất để truy cứu: chính là người quét bước sau (BRD §9)
    closed_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("app_user.id"))

    round: Mapped[MoRound] = relationship(back_populates="steps")
