"""Bảng `manufacturing_order` — lệnh sản xuất, gốc của mọi thứ."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.base import Base, _uuid_pk, mo_status_enum
from app.common.vocab.enums import MoStatus

if TYPE_CHECKING:  # tránh vòng import — SQLAlchemy tra tên lớp lúc chạy, không cần import thật
    from app.modules.round.models import MoRound


class ManufacturingOrder(Base):
    """Nhập sai sau Submit thì HUỶ kèm lý do rồi tạo lệnh mới (BRD §4A).

    Không sửa, không xoá: mã đã thành QR và đã đi xuống xưởng.
    """

    __tablename__ = "manufacturing_order"
    id: Mapped[uuid.UUID] = _uuid_pk()
    code: Mapped[str] = mapped_column(String(16), nullable=False, unique=True)
    product_name: Mapped[str] = mapped_column(Text, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit: Mapped[str] = mapped_column(Text, nullable=False, default="PCS")
    pcs_per_box: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    required_production_sec: Mapped[int] = mapped_column(Integer, nullable=False)

    status: Mapped[MoStatus] = mapped_column(mo_status_enum, nullable=False,
                                             default=MoStatus.DRAFT)
    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("app_user.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                 nullable=False, server_default=func.now())
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cancelled_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("app_user.id"))
    cancel_reason_text: Mapped[str | None] = mapped_column(Text)

    rounds: Mapped[list[MoRound]] = relationship(back_populates="mo", order_by="MoRound.round_no")
