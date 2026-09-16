"""Ba bảng của trạm 4 — Sản xuất.

`production` là sổ chốt (1-1 với vòng); `line_segment` và `hourly_output` thì
nhiều dòng mỗi vòng. Thứ tự class giữ đúng thứ tự bảng trong DB-GON.md.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, SmallInteger, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.common.base import Base, _uuid_pk, segment_kind_enum
from app.common.vocab.enums import SegmentKind


class Production(Base):
    __tablename__ = "production"
    round_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("mo_round.id", ondelete="CASCADE"), primary_key=True)
    qty_ok: Mapped[int] = mapped_column(Integer, nullable=False)
    qty_ng: Mapped[int] = mapped_column(Integer, nullable=False)
    qty_short: Mapped[int] = mapped_column(Integer, nullable=False)
    ng_reason_code_id: Mapped[int | None] = mapped_column(ForeignKey("reason_code.id"))
    ng_reason_text: Mapped[str | None] = mapped_column(Text)
    short_reason_code_id: Mapped[int | None] = mapped_column(ForeignKey("reason_code.id"))
    short_reason_text: Mapped[str | None] = mapped_column(Text)
    closed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                nullable=False, server_default=func.now())
    closed_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("app_user.id"), nullable=False)


class LineSegment(Base):
    __tablename__ = "line_segment"
    id: Mapped[uuid.UUID] = _uuid_pk()
    round_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("mo_round.id", ondelete="CASCADE"), nullable=False)
    line_id: Mapped[int] = mapped_column(ForeignKey("line.id"), nullable=False)
    kind: Mapped[SegmentKind] = mapped_column(segment_kind_enum, nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                 nullable=False, server_default=func.now())
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    started_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("app_user.id"), nullable=False)
    ended_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("app_user.id"))
    hold_reason_code_id: Mapped[int | None] = mapped_column(ForeignKey("reason_code.id"))
    hold_reason_text: Mapped[str | None] = mapped_column(Text)


class HourlyOutput(Base):
    __tablename__ = "hourly_output"
    id: Mapped[uuid.UUID] = _uuid_pk()
    round_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("mo_round.id", ondelete="CASCADE"), nullable=False)
    work_date: Mapped[date] = mapped_column(Date, nullable=False)
    slot_hour: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    headcount: Mapped[int | None] = mapped_column(Integer)
    target_qty: Mapped[int | None] = mapped_column(Integer)
    qty: Mapped[int] = mapped_column(Integer, nullable=False)
    note: Mapped[str | None] = mapped_column(Text)
    recorded_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("app_user.id"), nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                  nullable=False, server_default=func.now())
