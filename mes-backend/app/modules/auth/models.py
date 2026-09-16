"""Bảng `app_user` và `refresh_token`.

`refresh_token` là bảng HẠ TẦNG, không thuộc 14 sổ nghiệp vụ — nó phục vụ việc
đăng nhập, không ghi lại chuyện gì xảy ra với lệnh sản xuất.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from app.common.base import Base, _uuid_pk


class AppUser(Base):
    """Người dùng. KHÔNG xoá, chỉ tắt `is_active` — mọi bảng đều trỏ FK về đây."""

    __tablename__ = "app_user"
    id: Mapped[uuid.UUID] = _uuid_pk()
    full_name: Mapped[str] = mapped_column(Text, nullable=False)
    emp_code: Mapped[str | None] = mapped_column(Text, unique=True)
    pin_hash: Mapped[str | None] = mapped_column(Text)
    roles: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class RefreshToken(Base):
    """Một refresh token đã phát. LƯU BẰNG BĂM, không lưu chuỗi gốc.

    Rò CSDL thì kẻ đọc được cũng không dựng lại được token — giống `pin_hash`.

    `used_at` là cột quan trọng nhất: refresh dùng MỘT LẦN rồi đổi cái mới. Thấy
    một token đã `used_at` mà lại được gửi lên lần nữa nghĩa là có người giữ bản
    sao — lúc đó thu hồi CẢ CHUỖI của người đó, xem `auth/service.py`.
    """

    __tablename__ = "refresh_token"
    id: Mapped[uuid.UUID] = _uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("app_user.id", ondelete="CASCADE"), nullable=False
    )
    token_hash: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Rỗng = còn dùng được. Có giá trị = đã đổi lấy access mới, không dùng lại được.
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Rỗng = chưa thu hồi. Có giá trị = đăng xuất, hoặc bị thu hồi cả chuỗi.
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Token nào thay thế nó — để lần ngược cả chuỗi khi cần thu hồi.
    replaced_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("refresh_token.id"))
