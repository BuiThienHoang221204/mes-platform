"""Cookie chứa token: thuộc tính, phạm vi, và xoá khi đăng xuất.

Không cần CSDL — chỉ dựng Response rồi đọc header Set-Cookie.
"""

from __future__ import annotations

from fastapi import Response

from app.common.config import settings
from app.common.security.cookies import (
    COOKIE_ACCESS,
    COOKIE_REFRESH,
    clear_token_cookies,
    set_token_cookies,
)


def _set_cookie_headers(r: Response) -> dict[str, str]:
    """Gom các header Set-Cookie thành {tên cookie: nguyên văn header}."""
    out = {}
    for name, value in r.raw_headers:
        if name == b"set-cookie":
            raw = value.decode()
            out[raw.split("=", 1)[0]] = raw
    return out


def test_ca_hai_cookie_deu_HTTPONLY():
    """JavaScript đọc được token thì mọi lý do dùng cookie sụp đổ."""
    r = Response()
    set_token_cookies(r, access="A", refresh="R")
    cookies = _set_cookie_headers(r)
    assert "HttpOnly" in cookies[COOKIE_ACCESS]
    assert "HttpOnly" in cookies[COOKIE_REFRESH]


def test_refresh_chi_gui_toi_nhom_auth():
    """Request thường KHÔNG mang refresh theo — nó chỉ tới /v1/auth."""
    r = Response()
    set_token_cookies(r, access="A", refresh="R")
    cookies = _set_cookie_headers(r)
    assert "Path=/v1/auth" in cookies[COOKIE_REFRESH]
    assert "Path=/;" in cookies[COOKIE_ACCESS] or cookies[COOKIE_ACCESS].endswith("Path=/")


def test_han_cookie_khop_han_token():
    """Cookie sống lâu hơn token thì trình duyệt gửi lên token đã chết."""
    r = Response()
    set_token_cookies(r, access="A", refresh="R")
    cookies = _set_cookie_headers(r)
    assert f"Max-Age={settings.jwt.access_ttl_minutes * 60}" in cookies[COOKIE_ACCESS]
    assert f"Max-Age={settings.jwt.refresh_ttl_days * 86400}" in cookies[COOKIE_REFRESH]


def test_dang_xuat_xoa_ca_hai_cookie():
    r = Response()
    clear_token_cookies(r)
    cookies = _set_cookie_headers(r)
    assert "Max-Age=0" in cookies[COOKIE_ACCESS]
    assert "Max-Age=0" in cookies[COOKIE_REFRESH]
    # Xoá phải dùng ĐÚNG path lúc đặt, không thì trình duyệt giữ nguyên cookie cũ
    assert "Path=/v1/auth" in cookies[COOKIE_REFRESH]


def test_samesite_none_thi_bat_buoc_secure():
    """SameSite=None mà không Secure thì trình duyệt vứt cookie — im lặng."""
    if settings.cookie.samesite == "none":
        assert settings.cookie.secure, "SameSite=none buộc phải MES_COOKIE_SECURE=true"
