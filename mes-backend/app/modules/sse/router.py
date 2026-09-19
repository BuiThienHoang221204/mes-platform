"""SSE endpoint — push thay đổi theo trạm.

GET /v1/sse/{station}
  Kết nối dài, server push mỗi khi hàng đợi hoặc danh sách tại trạm thay đổi.
  Auth bằng cookie httpOnly (same-site), giống mọi REST endpoint.

Protocol:
  event: queue:changed     — hàng đợi hoặc lệnh tại trạm thay đổi
  data: {"type":"changed","station":2}
  \n\n

  event: keepalive         — mỗi N giây, giữ kết nối sống qua proxy/load balancer
  data: {}
  \n\n

Auth: cookie httpOnly (`mes_access`) hoặc Bearer token.
EventSource API không set custom headers được, nên cookie là primary method.
"""

from __future__ import annotations

import asyncio
import json
import logging

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from app.common import event_bus
from app.common.config import settings
from app.db.session import SessionLocal
from app.common.errors import Unauthenticated
from app.common.security.cookies import COOKIE_ACCESS
from app.common.security.tokens import decode
from app.modules.auth import repository as auth_repo

router = APIRouter(tags=["sse"])
log = logging.getLogger("mes.sse")

KEEPALIVE = settings.sse.keepalive


def _authenticate(request: Request) -> None:
    """Xác thực từ cookie hoặc Authorization header. Ném Unauthenticated nếu sai."""
    token = request.cookies.get(COOKIE_ACCESS)
    if not token:
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
    if not token:
        raise Unauthenticated("Thiếu token — đăng nhập lại")

    payload = decode(token)
    if payload.get("typ") != "user":
        raise Unauthenticated("Token này không phải token người dùng")

    db = SessionLocal()
    try:
        user = auth_repo.get_user_by_id(db, payload["sub"])
        if user is None or not user.is_active:
            raise Unauthenticated("Tài khoản không còn hiệu lực")
    finally:
        db.close()


@router.get("/sse/{station}")
async def sse_stream(station: int, request: Request):
    """SSE stream cho một trạm. Push khi hàng đợi hoặc lệnh tại trạm thay đổi.

    Kết nối sẽ giữ cho đến khi client ngắt hoặc server shutdown.
    Mỗi 15s gửi keepalive để proxy/load balancer không timeout.
    """
    if station < 0 or station > 5:
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=400, content={"message": "Trạm không hợp lệ"})

    # Xác thực ngay, không giữ DB session
    try:
        _authenticate(request)
    except Unauthenticated as e:
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=401, content={"message": str(e)})

    topic = f"station:{station}"
    queue: asyncio.Queue = asyncio.Queue(maxsize=64)

    unsub = event_bus.subscribe_async(topic, queue)

    async def event_generator():
        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    data = await asyncio.wait_for(queue.get(), timeout=KEEPALIVE)
                    yield f"event: queue:changed\ndata: {json.dumps(data)}\n\n"
                except asyncio.TimeoutError:
                    yield f"event: keepalive\ndata: {json.dumps({})}\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            unsub()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
