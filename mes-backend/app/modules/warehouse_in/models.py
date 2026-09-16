"""Bảng `warehouse_in` — sổ trạm 5 (Nhập kho). 1-1 với vòng.

Đếm lại là TUỲ CHỌN: để trống thì lấy SL đã đóng thùng. Đây là nơi MO đóng lại
hoặc mở vòng mới, nên cột ở đây ít mà hệ quả thì lớn.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.common.base import Base


class WarehouseIn(Base):
    __tablename__ = "warehouse_in"
    round_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("mo_round.id", ondelete="CASCADE"), primary_key=True)
    qty_received: Mapped[int | None] = mapped_column(Integer)
    counted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    counted_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("app_user.id"))
