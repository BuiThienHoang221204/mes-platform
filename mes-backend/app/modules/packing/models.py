"""Hai bảng của công đoạn Đóng thùng.

    packing          sổ chốt, 1-1 với vòng — `qty_packed` là con số đẩy tiến độ MO
    packing_hourly   nhật ký trong ca, nhiều dòng mỗi vòng — đếm THÙNG

Chạy SONG SONG với Sản xuất, không phải bước nối tiếp. `qty_packed` mới là con số đẩy
tiến độ MO, không phải `production.qty_ok` (§6b.2).
"""

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, SmallInteger, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.common.base import Base, _uuid_pk


class Packing(Base):
    __tablename__ = "packing"
    round_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("mo_round.id", ondelete="CASCADE"), primary_key=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                 nullable=False, server_default=func.now())
    started_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("app_user.id"), nullable=False)
    qty_packed: Mapped[int | None] = mapped_column(Integer)
    note_text: Mapped[str | None] = mapped_column(Text)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("app_user.id"))


class PackingHourly(Base):
    """Mỗi khung giờ đóng được bao nhiêu THÙNG ĐẦY.

    `pcs_per_box` ĐÓNG DẤU vào từng dòng chứ không đọc sang `manufacturing_order`:
    quy cách bị sửa một lần là mọi dòng cũ quy ra số pcs khác. Cùng lý lẽ với
    `mo_round.target_qty`.

    Không có cột hàng lẻ — `lẻ = đã làm ra − Σ(boxes × pcs_per_box)` suy ra được,
    và nó KHÔNG phải `production.qty_short`.
    """

    __tablename__ = "packing_hourly"
    id: Mapped[uuid.UUID] = _uuid_pk()
    round_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("mo_round.id", ondelete="CASCADE"), nullable=False)
    work_date: Mapped[date] = mapped_column(Date, nullable=False)
    slot_hour: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    boxes: Mapped[int] = mapped_column(Integer, nullable=False)
    pcs_per_box: Mapped[int] = mapped_column(Integer, nullable=False)
    note: Mapped[str | None] = mapped_column(Text)
    recorded_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("app_user.id"), nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                  nullable=False, server_default=func.now())
