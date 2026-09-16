"""Truy vấn nhật ký `mo_event` — CHỈ GHI THÊM.

    log(db, ..., action=Act.X)             ghi một dòng nhật ký
    events_of(db, mo_id, limit=500)        đọc theo thứ tự mới nhất trước

Không có hàm sửa hay xoá, và cũng không thể có: RULE ở DB chặn UPDATE/DELETE.
9/10 service đều gọi `log` — đây là thứ dùng chung nhất của cả hệ thống.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.event_log.models import MoEvent
from app.common.vocab.action_codes import Act


def log(db: Session, *, mo_id: uuid.UUID, action: Act, round_id: uuid.UUID | None = None,
        step_no: int | None = None, from_state: str | None = None,
        to_state: str | None = None, reason: str | None = None,
        actor_id: uuid.UUID | None = None) -> None:
    """Ghi một dòng nhật ký. Không có hàm sửa/xoá — RULE ở DB chặn.

    `action` nhận `Act` chứ không nhận `str`: cột dưới CSDL là `text` trần, không
    CHECK, nên một chuỗi gõ sai nằm lại sổ vĩnh viễn. Xem `action_codes.py`.
    """
    db.add(MoEvent(mo_id=mo_id, round_id=round_id, step_no=step_no, action=action,
                   from_state=from_state, to_state=to_state, reason_text=reason,
                   actor_id=actor_id))


def events_of(db: Session, mo_id: uuid.UUID, limit: int = 500) -> list[MoEvent]:
    """Nhật ký của một MO, mới nhất trước, mặc định 500 dòng gần nhất."""
    return list(db.scalars(
        select(MoEvent).where(MoEvent.mo_id == mo_id)
        .order_by(MoEvent.occurred_at.desc(), MoEvent.id.desc()).limit(limit)
    ))
