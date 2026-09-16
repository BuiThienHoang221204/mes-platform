"""Bảng `scan_dedupe` — HẠ TẦNG, KHÔNG thuộc 14 sổ nghiệp vụ.

Để riêng một file có tên rõ ràng để lần sau đếm bảng không bị lệch với
DB-GON.md: 14 file kia là 14 sổ, file này là bảng kỹ thuật.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, SmallInteger, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.common.base import Base


class ScanDedupe(Base):
    """Đầu đọc hay bắn hai lần, FE có thể bị F5 giữa chừng — chặn ở server.

    Khoá theo MÃ + TRẠM chứ không chỉ theo mã: cùng một MO quét tiếp ở trạm kế
    bên phải ăn ngay (BRD §1b.3).
    """

    __tablename__ = "scan_dedupe"
    mo_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("manufacturing_order.id", ondelete="CASCADE"), primary_key=True)
    station_no: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    scanned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                 nullable=False, server_default=func.now())
    result_message: Mapped[str] = mapped_column(Text, nullable=False, default="")
