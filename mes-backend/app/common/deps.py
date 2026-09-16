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

from app.common.errors import Forbidden, NotFound
from app.common.security.actor import Actor
from app.common.security.cookies import COOKIE_ACCESS
from app.common.security.tokens import decode
from app.db.session import get_db
from app.modules.auth import repository as auth_repo

DbDep = Annotated[Session, Depends(get_db)]

# `auto_error=False` ở cả ba: thiếu thì trả None để tự ghép, chứ không để FastAPI
# ném 403 với câu tiếng Anh mặc định — người ở xưởng đọc câu tiếng Việt của mình.
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
        raise Forbidden("Thiếu token — đăng nhập lại")

    payload = decode(token)
    if payload.get("typ") != "user":
        raise Forbidden("Token này không phải token người dùng")

    # Đọc lại người dùng ở MỌI request: tắt `is_active` là chặn ngay, không phải
    # đợi token hết hạn. Đây là lý do access token không cần thu hồi riêng.
    user = auth_repo.get_user_by_id(db, payload["sub"])
    if user is None or not user.is_active:
        raise NotFound("Tài khoản không còn hiệu lực")
    actor = Actor(user_id=str(user.id), full_name=user.full_name, roles=tuple(user.roles))

    # ĐÓNG giao dịch chỉ-đọc mà câu SELECT trên vừa tự mở. Không đóng thì router
    # gọi `with db.begin()` là gặp "A transaction is already begun on this Session"
    # — tức MỌI endpoint ghi đều hỏng. Đọc xong giá trị rồi mới rollback, vì
    # rollback làm hết hạn đối tượng ORM.
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
        raise Forbidden("Thiết bị chưa đăng ký trạm — thiếu X-Station-Token")
    payload = decode(token)
    if payload.get("typ") != "station":
        raise Forbidden("Token này không phải token trạm")
    return int(payload["station"])


ActorDep = Annotated[Actor, Depends(current_actor)]
StationDep = Annotated[int, Depends(current_station)]
