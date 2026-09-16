"""Bảng `mo_event` — nhật ký, CHỈ GHI THÊM.

Migration đặt RULE chặn UPDATE và DELETE: nhật ký sửa được thì không còn là nhật ký.
Bảng duy nhất dùng BigInteger tự tăng — ghi nhiều, đọc theo thời gian.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, SmallInteger, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.common.base import Base


class MoEvent(Base):
    __tablename__ = "mo_event"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    mo_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("manufacturing_order.id"), nullable=False)
    # rỗng được: tạo lệnh / Submit / huỷ xảy ra TRƯỚC khi có vòng nào
    round_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("mo_round.id"))
    step_no: Mapped[int | None] = mapped_column(SmallInteger)
    action: Mapped[str] = mapped_column(Text, nullable=False)
    from_state: Mapped[str | None] = mapped_column(Text)
    to_state: Mapped[str | None] = mapped_column(Text)
    reason_text: Mapped[str | None] = mapped_column(Text)
    actor_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("app_user.id"))
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                  nullable=False, server_default=func.now())
