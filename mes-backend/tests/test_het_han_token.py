"""Token hết hạn phải là 401, thiếu quyền mới là 403.

Trình duyệt chỉ đổi refresh lấy access mới khi thấy **401**. Trả 403 cho token hết
hạn thì sau 15 phút mọi lời gọi đều hỏng, trong khi refresh token còn sống bảy
ngày mà không ai dùng tới — người ở xưởng thấy màn hình đỏ giữa ca mà không hiểu
vì sao.
"""

from __future__ import annotations

import uuid
from datetime import timedelta

import jwt
import pytest
from fastapi.testclient import TestClient

from app.common.config import settings
from app.common.security.cookies import COOKIE_ACCESS
from app.common.vocab.error_codes import Err


@pytest.fixture
def client(db):
    """KHÔNG tiêm `current_actor` — test này đo chính lớp xác thực."""
    from app.db.session import get_db
    from app.main import app

    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def _token(user_id: uuid.UUID, *, minutes: int, typ: str = "user") -> str:
    from app.common.clock import now

    return jwt.encode(
        {"sub": str(user_id), "typ": typ, "exp": now() + timedelta(minutes=minutes)},
        settings.jwt.secret,
        algorithm="HS256",
    )


def test_thieu_token_tra_401(client):
    res = client.get("/v1/mos")

    assert res.status_code == 401, res.text
    assert res.json()["code"] == Err.UNAUTHENTICATED


def test_token_het_han_tra_401(client, actor):
    client.cookies.set(COOKIE_ACCESS, _token(actor, minutes=-1))

    res = client.get("/v1/mos")

    assert res.status_code == 401, res.text
    assert res.json()["code"] == Err.UNAUTHENTICATED


def test_token_con_han_thi_vao_duoc(client, actor):
    client.cookies.set(COOKIE_ACCESS, _token(actor, minutes=15))

    assert client.get("/v1/mos").status_code == 200


def test_token_sai_chu_ky_tra_401(client, actor):
    good = _token(actor, minutes=15)
    client.cookies.set(COOKIE_ACCESS, good[:-4] + "xxxx")

    assert client.get("/v1/mos").status_code == 401


def test_token_tram_dung_lam_token_nguoi_tra_401(client):
    client.cookies.set(COOKIE_ACCESS, _token(uuid.uuid4(), minutes=15, typ="station"))

    res = client.get("/v1/mos")

    assert res.status_code == 401, res.text
    assert res.json()["code"] == Err.UNAUTHENTICATED


def test_refresh_khong_co_cookie_tra_401(client):
    res = client.post("/v1/auth/refresh")

    assert res.status_code == 401, res.text
    assert res.json()["code"] == Err.UNAUTHENTICATED


def test_THIEU_QUYEN_van_la_403_chu_khong_phai_401(db, actor):
    """Ranh giới của cả bài: sai vai thì lấy token mới cũng vô ích, đừng bảo client refresh."""
    from app.common.deps import current_actor
    from app.common.security.actor import Actor
    from app.db.session import get_db
    from app.main import app

    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[current_actor] = lambda: Actor(
        user_id=str(actor), full_name="Thợ QC", roles=("QC_MEMBER",)
    )
    try:
        with TestClient(app) as c:
            res = c.post("/v1/mos", json={
                "code": "M900001", "product_name": "Vỏ", "quantity": 10,
                "required_production_min": 30,
            })
        assert res.status_code == 403, res.text
        assert res.json()["code"] == Err.FORBIDDEN
    finally:
        app.dependency_overrides.clear()
