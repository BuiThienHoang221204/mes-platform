"""Bảng `warehouse_out` — sổ trạm 0 (Kho bàn giao). 1-1 với vòng.

Chỉ còn MỘT thao tác: bàn giao. Bước in phiếu đã bỏ để giảm thao tác cho Kho.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from app.common.base import Base


class WarehouseOut(Base):
    __tablename__ = "warehouse_out"
    round_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("mo_round.id", ondelete="CASCADE"), primary_key=True)
    handed_over_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                     nullable=False, server_default=func.now())
    handed_over_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("app_user.id"), nullable=False)
