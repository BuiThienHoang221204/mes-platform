"""Truy vấn `app_user` và `refresh_token`.

    get_user_by_emp_code(db, emp_code)       tra theo mã nhân viên
    get_user_by_id(db, user_id)              tra theo id trong token
    save_refresh(db, user_id, hash, …)       ghi một refresh vừa phát
    find_refresh(db, token_hash)             tra token gửi lên, có KHOÁ DÒNG
    revoke_all_for_user(db, user_id)         hạ toàn bộ refresh còn sống của một người

Hai hàm tra người trả None khi không thấy, KHÔNG ném lỗi: câu cho "sai mã" và
"sai PIN" nên giống nhau để không lộ mã nhân viên nào có thật.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.common.clock import now
from app.modules.auth.models import AppUser, RefreshToken


def get_user_by_emp_code(db: Session, emp_code: str) -> AppUser | None:
    """Tra người theo mã nhân viên. None = không có — người gọi tự quyết câu trả về."""
    return db.scalar(select(AppUser).where(AppUser.emp_code == emp_code))


def get_user_by_id(db: Session, user_id: uuid.UUID | str) -> AppUser | None:
    """Tra người theo id lấy từ token. None = tài khoản đã bị xoá khỏi bảng."""
    return db.scalar(select(AppUser).where(AppUser.id == user_id))


def save_refresh(
    db: Session, *, user_id: uuid.UUID, token_hash: str, expires_at: datetime
) -> RefreshToken:
    """Ghi một refresh vừa phát. `issued_at` lấy giờ của DB."""
    row = RefreshToken(
        user_id=user_id, token_hash=token_hash, issued_at=now(), expires_at=expires_at
    )
    db.add(row)
    db.flush()
    return row


def find_refresh(db: Session, token_hash: str) -> RefreshToken | None:
    """Tra token gửi lên, CÓ KHOÁ DÒNG.

    Khoá vì hai request refresh cùng lúc trên cùng một token phải có đúng một cái
    thắng — không khoá thì cả hai đọc thấy `used_at` rỗng và cùng phát token mới.
    """
    return db.scalar(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash).with_for_update()
    )


def revoke_all_for_user(db: Session, user_id: uuid.UUID) -> int:
    """Hạ MỌI refresh còn sống của một người. Trả số dòng bị hạ.

    Gọi khi phát hiện token đã dùng lại được gửi lên lần nữa: không biết bản sao
    nằm ở đâu, nên cắt sạch và bắt đăng nhập lại.

    Đếm bằng `RETURNING` chứ không bằng `rowcount`: con số này đi thẳng vào câu
    báo cho người dùng ("đã thu hồi N phiên"), mà `rowcount` là thuộc tính của
    con trỏ driver — mỗi driver một kiểu, có chỗ trả -1. `RETURNING` là hàng
    THẬT vừa bị hạ, Postgres trả về trong cùng một lượt đi.
    """
    revoked = db.scalars(
        update(RefreshToken)
        .where(
            RefreshToken.user_id == user_id,
            RefreshToken.revoked_at.is_(None),
        )
        .values(revoked_at=now())
        .returning(RefreshToken.id)
    ).all()
    return len(revoked)
