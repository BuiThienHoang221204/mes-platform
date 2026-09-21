"""Dependency dùng chung cho router.

    DbDep       phiên CSDL
    ActorDep    ai đang bấm — đọc access token
    StationDep  đang đứng ở trạm nào — đọc token của THIẾT BỊ

Ba cách gửi token, khai thành ba `security scheme` để trang /docs dựng được nút
**Authorize**: cookie `mes_access` (trình duyệt), header `Authorization: Bearer`
(curl, máy quét), và header `X-Station-Token` (thiết bị ở trạm).

Access token đọc từ COOKIE trước, thiếu mới xét header. Giữ cả hai vì trình duyệt
dùng cookie, còn /docs, curl và máy quét thì gửi header.
"""

from __future__ import annotations

import threading
import time
from typing import Annotated

from fastapi import Depends
from fastapi.security import APIKeyCookie, APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.common.config import settings
from app.common.errors import NotFound, Unauthenticated
from app.common.security.actor import Actor
from app.common.security.cookies import COOKIE_ACCESS
from app.common.security.tokens import decode
from app.db.session import get_db
from app.modules.auth import repository as auth_repo

DbDep = Annotated[Session, Depends(get_db)]

PAGE_SIZE = 10
PAGE_MAX = 100

def page_params(limit: int = PAGE_SIZE, offset: int = 0) -> tuple[int, int]:
    """Kẹp hai đầu NGAY TẠI CỬA, không để service phải nhớ làm việc đó.

    `limit=999999` là một lượt quét sạch bảng, và với endpoint có cache thì còn là
    một mục nằm lại trong bộ nhớ. `offset` âm làm Postgres ném lỗi cú pháp.
    """
    return max(1, min(limit, PAGE_MAX)), max(0, offset)

PageDep = Annotated[tuple[int, int], Depends(page_params)]

_ACTOR_MAX = 512
_actor_lock = threading.Lock()
_actor_cache: dict[str, tuple[float, Actor]] = {}


def forget_actor(user_id: str | None = None) -> None:
    """Quên ngay một người, hoặc quên tất cả khi không nói ai.

    Đường thoát cho lúc khoá tài khoản: không gọi thì phải đợi hết
    `MES_AUTH_ACTOR_CACHE_TTL`. Test dùng bản không tham số.
    """
    with _actor_lock:
        if user_id is None:
            _actor_cache.clear()
        else:
            _actor_cache.pop(str(user_id), None)


def _actor_from_cache(sub: str) -> Actor | None:
    hit = _actor_cache.get(sub)
    if hit is None or hit[0] <= time.monotonic():
        return None
    return hit[1]


def _remember_actor(sub: str, actor: Actor) -> None:
    ttl = settings.auth.actor_cache_ttl
    if ttl <= 0:
        return
    now = time.monotonic()
    with _actor_lock:
        _actor_cache[sub] = (now + ttl, actor)
        if len(_actor_cache) <= _ACTOR_MAX:
            return
        for stale in [k for k, v in list(_actor_cache.items()) if v[0] <= now]:
            _actor_cache.pop(stale, None)
        if len(_actor_cache) > _ACTOR_MAX:
            _actor_cache.clear()


cookie_scheme = APIKeyCookie(
    name=COOKIE_ACCESS,
    auto_error=False,
    scheme_name="cookie",
    description="Cookie httpOnly, trình duyệt tự gửi sau khi gọi /v1/auth/login. "
    "Không cần điền gì ở đây — Swagger không đặt được cookie httpOnly.",
)
bearer_scheme = HTTPBearer(
    auto_error=False,
    scheme_name="bearer",
    description="Access token dán vào đây khi gọi bằng curl hoặc từ máy quét. "
    "Lấy bằng cách xem header Set-Cookie của /v1/auth/login.",
)
station_scheme = APIKeyHeader(
    name="X-Station-Token",
    auto_error=False,
    scheme_name="station",
    description="Token của THIẾT BỊ đặt ở trạm, lấy từ /v1/auth/station-token. "
    "Chỉ /v1/scan cần.",
)

def current_actor(
    db: DbDep,
    cookie_token: Annotated[str | None, Depends(cookie_scheme)] = None,
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)] = None,
) -> Actor:
    token = cookie_token or (creds.credentials if creds else None)
    if not token:
        raise Unauthenticated("Thiếu token — đăng nhập lại")

    payload = decode(token)
    if payload.get("typ") != "user":
        raise Unauthenticated("Token này không phải token người dùng")

    sub = str(payload["sub"])
    known = _actor_from_cache(sub)
    if known is not None:
        return known

    user = auth_repo.get_user_by_id(db, sub)
    if user is None or not user.is_active:
        raise NotFound("Tài khoản không còn hiệu lực")
    actor = Actor(user_id=str(user.id), full_name=user.full_name, roles=tuple(user.roles))
    _remember_actor(sub, actor)

    db.rollback()
    return actor

def current_station(
    token: Annotated[str | None, Depends(station_scheme)] = None,
) -> int:
    """Trạm lấy từ THIẾT BỊ, không lấy từ body.

    BRD §1b.3: mã QR chỉ nói MO nào, không nói bước nào. Để client tự khai trạm
    thì một máy giả được mọi trạm.

    Dùng header chứ không cookie: token này nạp một lần vào máy đặt cố định ở
    trạm, không đi qua màn hình đăng nhập của ai cả.
    """
    if not token:
        raise Unauthenticated("Thiết bị chưa đăng ký trạm — thiếu X-Station-Token")
    payload = decode(token)
    if payload.get("typ") != "station":
        raise Unauthenticated("Token này không phải token trạm")
    return int(payload["station"])

ActorDep = Annotated[Actor, Depends(current_actor)]
StationDep = Annotated[int, Depends(current_station)]
