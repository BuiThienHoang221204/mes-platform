"""Hai danh mục ít đổi: `line` (14 chuyền) và `reason_code`."""

from __future__ import annotations

from sqlalchemy import Boolean, SmallInteger, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.common.base import Base, reason_group_enum
from app.common.vocab.enums import ReasonGroup


class Line(Base):
    __tablename__ = "line"
    id: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    code: Mapped[str] = mapped_column(Text, nullable=False, unique=True)  # 'L01'
    name: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class ReasonCode(Base):
    __tablename__ = "reason_code"
    id: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    group_code: Mapped[ReasonGroup] = mapped_column(reason_group_enum, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
