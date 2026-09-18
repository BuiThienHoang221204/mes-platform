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

from typing import Annotated

from fastapi import Depends
from fastapi.security import APIKeyCookie, APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

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

    user = auth_repo.get_user_by_id(db, payload["sub"])
    if user is None or not user.is_active:
        raise NotFound("Tài khoản không còn hiệu lực")
    actor = Actor(user_id=str(user.id), full_name=user.full_name, roles=tuple(user.roles))

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
