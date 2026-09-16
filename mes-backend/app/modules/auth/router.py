"""Đăng nhập và cấp token. Không thuộc trạm nào.

    POST /auth/login                   mã nhân viên + PIN → đặt cookie access + refresh
    POST /auth/refresh                 đọc refresh từ cookie, đổi lấy cặp MỚI
    POST /auth/logout                  thu hồi refresh và xoá cookie
    POST /auth/station-token           token gắn vào THIẾT BỊ đặt ở trạm · chỉ Planner

Token đặt vào cookie httpOnly, KHÔNG trả trong body — JavaScript của trang không
đọc được thì một lỗ XSS cũng không lấy được token.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Cookie, Response

from app.common.deps import ActorDep, DbDep
from app.common.errors import Forbidden
from app.common.schemas import OkOut
from app.common.security.cookies import COOKIE_REFRESH, clear_token_cookies, set_token_cookies
from app.common.security.permissions import PLANNER
from app.common.security.tokens import make_station_token
from app.modules.auth import service as auth_service
from app.modules.auth.schemas import LoginIn, SessionOut, StationTokenOut

router = APIRouter(tags=["auth"])


@router.post("/auth/login", response_model=SessionOut)
def login(body: LoginIn, response: Response, db: DbDep) -> SessionOut:
    """Đăng nhập bằng mã nhân viên + PIN. Token đặt vào cookie, không trả trong body."""
    pair = auth_service.login(db, emp_code=body.emp_code, pin=body.pin)
    set_token_cookies(response, access=pair.access_token, refresh=pair.refresh_token)
    return SessionOut(full_name=pair.full_name, roles=pair.roles)


@router.post("/auth/refresh", response_model=SessionOut)
def refresh(
    response: Response, db: DbDep,
    mes_refresh: Annotated[str | None, Cookie()] = None,
) -> SessionOut:
    """Đổi refresh trong cookie lấy cặp MỚI. Cookie cũ bị ghi đè ngay.
    Gửi lại một refresh đã dùng = thu hồi toàn bộ phiên của người đó."""
    if not mes_refresh:
        raise Forbidden("Thiếu phiên đăng nhập — đăng nhập lại")
    pair = auth_service.refresh(db, refresh_raw=mes_refresh)
    set_token_cookies(response, access=pair.access_token, refresh=pair.refresh_token)
    return SessionOut(full_name=pair.full_name, roles=pair.roles)


@router.post("/auth/logout", response_model=OkOut)
def logout(
    response: Response, db: DbDep,
    mes_refresh: Annotated[str | None, Cookie()] = None,
) -> OkOut:
    """Thu hồi refresh rồi xoá cookie. Access còn sống tới khi hết hạn — tối đa 15 phút."""
    if mes_refresh:
        auth_service.logout(db, refresh_raw=mes_refresh)
    clear_token_cookies(response)
    return OkOut(message="Đã đăng xuất")


@router.post("/auth/station-token", response_model=StationTokenOut)
def station_token(station: int, actor: ActorDep) -> dict:
    """Cấp token gắn vào THIẾT BỊ đặt cố định ở trạm. Chỉ Planner được cấp.

    Trả trong body chứ không đặt cookie: token này nạp một lần vào máy ở trạm.
    """
    actor.require_role(PLANNER)
    return {"station": station, "token": make_station_token(station)}


assert COOKIE_REFRESH == "mes_refresh", "tên cookie và tên tham số phải khớp nhau"
