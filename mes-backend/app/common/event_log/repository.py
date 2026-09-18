"""Truy vấn nhật ký `mo_event` — CHỈ GHI THÊM.

    log(db, ..., action=Act.X)             ghi một dòng nhật ký
    events_of(db, mo_id, limit, offset)    đọc một TRANG, mới nhất trước
    count_events(db, mo_id)                tổng số dòng, để biết còn trang sau không

Không có hàm sửa hay xoá, và cũng không thể có: RULE ở DB chặn UPDATE/DELETE.
9/10 service đều gọi `log` — đây là thứ dùng chung nhất của cả hệ thống.
"""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
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


def events_of(db: Session, mo_id: uuid.UUID, *, limit: int, offset: int = 0) -> list[MoEvent]:
    """Một TRANG nhật ký, mới nhất trước.

    `limit` BẮT BUỘC truyền, không có mặc định. Hàm này trước đây mặc định 500 và
    tên nó đọc như "mọi dòng của MO"; đổi mặc định thành một trang là mọi chỗ gọi
    cũ âm thầm mất dòng mà không ai báo. Bắt khai rõ thì chỗ nào cần cả sổ vẫn lấy
    được cả sổ, chỗ nào phân trang thì nói ra là phân trang.

    Sắp theo `(occurred_at DESC, id DESC)` chứ không chỉ theo thời điểm: nhiều
    dòng sinh ra trong CÙNG một transaction có `occurred_at` bằng nhau tới từng
    micro giây, và thứ tự không xác định thì phân trang trả dòng trùng ở trang này
    rồi bỏ sót dòng khác ở trang sau. `id` là khoá phụ để thứ tự luôn xác định.
    """
    return list(db.scalars(
        select(MoEvent).where(MoEvent.mo_id == mo_id)
        .order_by(MoEvent.occurred_at.desc(), MoEvent.id.desc())
        .limit(limit).offset(offset)
    ))


def count_events(db: Session, mo_id: uuid.UUID) -> int:
    """Tổng số dòng nhật ký — màn hình cần biết còn trang sau hay không."""
    return db.scalar(
        select(func.count()).select_from(MoEvent).where(MoEvent.mo_id == mo_id)
    ) or 0
