"""SSE đi qua HTTP thật — chứng minh tin tới được client, và §12.4 áp cho đường này.

Ca đầu là ca mà A5 đã trượt suốt: `emit` gọi từ luồng KHÁC với event loop của app,
đúng như endpoint ghi chạy trong threadpool. Test ở tầng `event_bus` không đủ bắt —
phải đi qua đúng vòng đời `subscribe_async` của endpoint.
"""

from __future__ import annotations

import asyncio
import uuid

import pytest
from fastapi.testclient import TestClient

from app.common import event_bus
from app.common.security.actor import Actor
from app.common.security.permissions import PLANNER
from app.modules.sse import router as sse_router


def _actor(*roles: str) -> Actor:
    return Actor(user_id=str(uuid.uuid4()), full_name="Thợ T", roles=roles)


@pytest.fixture
def client(db, monkeypatch):
    from app.common.deps import current_actor
    from app.db.session import get_db
    from app.main import app

    monkeypatch.setattr(sse_router, "KEEPALIVE", 0.2)

    current = {"actor": _actor(PLANNER)}
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[current_actor] = lambda: current["actor"]

    with TestClient(app) as c:
        c.as_role = lambda *roles: current.update(actor=_actor(*roles))
        yield c

    app.dependency_overrides.clear()


def test_tin_phat_tu_luong_khac_toi_duoc_client():
    """Đúng vòng đời của endpoint: `subscribe_async` chạy trên event loop, `emit`
    chạy ở luồng khác — y như endpoint ghi trong threadpool."""

    class _FakeRequest:
        async def is_disconnected(self) -> bool:
            return False

    async def scenario():
        resp = await sse_router.sse_stream(
            station=2, request=_FakeRequest(), actor=_actor(PLANNER)
        )
        stream = resp.body_iterator
        try:
            await asyncio.to_thread(
                event_bus.emit, "station:2", {"type": "changed", "station": 2}
            )
            return await asyncio.wait_for(stream.__anext__(), timeout=5)
        finally:
            await stream.aclose()

    chunk = asyncio.run(scenario())
    assert "event: queue:changed" in chunk, f"nhận được {chunk!r} thay vì tin thật"
    assert '"station": 2' in chunk


def test_khong_dang_nhap_thi_khong_mo_duoc_stream(db):
    from app.db.session import get_db
    from app.main import app

    app.dependency_overrides[get_db] = lambda: db
    try:
        with TestClient(app) as c:
            assert c.get("/v1/sse/2").status_code == 401
    finally:
        app.dependency_overrides.clear()


def test_QC_khong_nghe_duoc_stream_cua_Kho(client):
    """§12.4 — ngoài trạm của mình và trạm 4 thì không thấy gì.

    Trước đây đường này tự viết phần xác thực nên nằm ngoài ma trận phân quyền:
    gõ thẳng `/v1/sse/0` là nghe được mọi thay đổi của Kho.
    """
    client.as_role("QC_MEMBER")
    assert client.get("/v1/sse/0").status_code == 403


def test_tram_khong_hop_le_bi_tu_choi(client):
    assert client.get("/v1/sse/9").status_code == 422
