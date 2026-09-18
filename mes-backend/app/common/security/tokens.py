"""Băm mã PIN, phát và đọc token.

Ba loại chuỗi bí mật, ba cách xử lý khác nhau — và khác nhau có lý do, đọc docstring
từng hàm:

    PIN             bcrypt          người đặt, ngắn, dò từ điển được
    access token    JWT ký HS256    ngắn hạn, không lưu ở đâu cả
    refresh token   chuỗi ngẫu nhiên + SHA-256, KHÔNG phải JWT
"""

from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import datetime, timedelta

import bcrypt
import jwt

from app.common.clock import now
from app.common.config import settings
from app.common.errors import Unauthenticated


def hash_pin(pin: str) -> str:
    """Băm mã PIN bằng bcrypt.

    Gọi thẳng thư viện `bcrypt` chứ không qua `passlib`: passlib 1.7.4 (bản cuối,
    2020) dò backend bằng một chuỗi thử dài hơn 72 byte, mà bcrypt 5.0 ném lỗi
    thay vì cắt bớt — cả hàm băm gãy ngay lúc gọi lần đầu.
    """
    return bcrypt.hashpw(pin.encode(), bcrypt.gensalt()).decode()


def verify_pin(pin: str, hashed: str) -> bool:
    """So PIN với chuỗi băm. Sai định dạng băm cũng trả False, không ném lỗi."""
    try:
        return bcrypt.checkpw(pin.encode(), hashed.encode())
    except ValueError:
        return False


def make_access_token(user_id: uuid.UUID | str) -> str:
    """Token đi kèm MỌI request. Ngắn hạn, không lưu ở đâu cả.

    Không thu hồi được một khi đã phát — nhưng không cần: `deps.current_actor`
    đọc lại bản ghi người dùng ở mỗi request, tắt `is_active` là chặn ngay.

    Nhận thẳng `UUID` và tự đổi sang chuỗi: claim `sub` của JWT buộc phải là chuỗi,
    mà đó là luật của JWT — để mỗi nơi gọi tự nhớ `str()` thì sót một chỗ là token
    hỏng lúc chạy.
    """
    payload = {"sub": str(user_id), "typ": "user",
               "exp": now() + timedelta(minutes=settings.jwt.access_ttl_minutes)}
    return jwt.encode(payload, settings.jwt.secret, algorithm="HS256")


def make_refresh_token() -> tuple[str, str, datetime]:
    """Sinh refresh token. Trả (chuỗi gốc, băm để lưu, hạn).

    KHÔNG phải JWT, mà là chuỗi ngẫu nhiên mờ đục. Hai lý do:
    lần refresh nào cũng phải tra CSDL (để xoay vòng và bắt dùng lại) nên chữ ký
    JWT chẳng tiết kiệm được gì; và lộ `jwt.secret` thì kẻ tấn công tự ký được
    JWT, còn chuỗi ngẫu nhiên thì không đoán ra.
    """
    raw = secrets.token_urlsafe(48)
    expires_at = now() + timedelta(days=settings.jwt.refresh_ttl_days)
    return raw, hash_token(raw), expires_at


def hash_token(raw: str) -> str:
    """SHA-256, KHÔNG phải bcrypt.

    Token đã là 48 byte ngẫu nhiên nên không có gì để dò từ điển — thứ bcrypt
    sinh ra để chống. Mà refresh chạy mỗi 15 phút trên mọi máy tính bảng, bcrypt
    ở đó là tự tạo nút thắt.
    """
    return hashlib.sha256(raw.encode()).hexdigest()


def make_station_token(station_no: int) -> str:
    """Token gắn vào THIẾT BỊ đặt cố định ở trạm, hạn dài."""
    payload = {"station": station_no, "typ": "station",
               "exp": now() + timedelta(days=settings.jwt.station_ttl_days)}
    return jwt.encode(payload, settings.jwt.secret, algorithm="HS256")


def decode(token: str) -> dict:
    try:
        return jwt.decode(token, settings.jwt.secret, algorithms=["HS256"])
    except jwt.PyJWTError as exc:  # noqa: BLE001
        raise Unauthenticated("Phiên đăng nhập không hợp lệ hoặc đã hết hạn") from exc
