"""Schemas cho trạm 0 — Kho xuất."""

from __future__ import annotations

from pydantic import BaseModel

from app.common.schemas import NoteText


class HandoverIn(BaseModel):
    """Payload khi bàn giao lệnh xuống xưởng."""
    note: NoteText | None = None
