"""Đặt và xoá cookie chứa token. MỘT chỗ duy nhất biết tên và thuộc tính cookie.

    set_token_cookies(response, access, refresh)   sau đăng nhập / làm mới
    clear_token_cookies(response)                  khi đăng xuất

Hai điều quan trọng của cookie ở đây:

`httponly=True` — JavaScript của trang KHÔNG đọc được token. Đây là lý do chính
để bỏ localStorage: một lỗ XSS thì localStorage bị đọc sạch, còn cookie httpOnly
thì không.

`path` của refresh hẹp hơn access — refresh CHỈ gửi tới nhóm /v1/auth. Request
thường không mang nó theo, nên nó ít lộ hơn hẳn.
"""

from __future__ import annotations

from fastapi import Response

from app.common.config import settings

COOKIE_ACCESS = "mes_access"
COOKIE_REFRESH = "mes_refresh"

# Refresh chỉ cần tới được /auth/refresh và /auth/logout.
REFRESH_PATH = "/v1/auth"


def set_token_cookies(response: Response, *, access: str, refresh: str) -> None:
    """Gắn cả hai cookie. Hạn của cookie đặt bằng đúng hạn của token bên trong."""
    _set(response, COOKIE_ACCESS, access, settings.jwt.access_ttl_minutes * 60, "/")
    _set(response, COOKIE_REFRESH, refresh, settings.jwt.refresh_ttl_days * 86400, REFRESH_PATH)


def clear_token_cookies(response: Response) -> None:
    """Xoá cookie ở trình duyệt. Việc thu hồi thật nằm ở `auth/service.logout`."""
    response.delete_cookie(COOKIE_ACCESS, path="/", domain=settings.cookie.domain)
    response.delete_cookie(COOKIE_REFRESH, path=REFRESH_PATH, domain=settings.cookie.domain)


def _set(response: Response, name: str, value: str, max_age_sec: int, path: str) -> None:
    response.set_cookie(
        key=name,
        value=value,
        max_age=max_age_sec,
        path=path,
        domain=settings.cookie.domain,
        httponly=True,
        secure=settings.cookie.secure,
        samesite=settings.cookie.samesite,
    )
