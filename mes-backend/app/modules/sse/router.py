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

Auth: đi qua `ActorDep` như mọi endpoint khác, rồi `require_step(station, VIEW)` —
§12.4 áp cho đường này y hệt `GET /board/queue/{station}`. Trước đây file này tự viết
lấy phần xác thực, nên nằm ngoài ma trận phân quyền và mở CSDL ngay trong `async def`,
chặn cả event loop mỗi lần có máy nối vào.

`ActorDep` đọc cookie trước rồi mới xét header, nên EventSource — vốn không set được
custom header — vẫn dùng được.
"""

from __future__ import annotations

import asyncio
import json
import logging

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from app.common import event_bus
from app.common.config import settings
from app.common.deps import ActorDep
from app.common.errors import Invalid
from app.common.security.permissions import VIEW
from app.common.vocab.enums import STEP_NAMES

router = APIRouter(tags=["sse"])
log = logging.getLogger("mes.sse")

KEEPALIVE = settings.sse.keepalive


@router.get("/sse/{station}")
async def sse_stream(station: int, request: Request, actor: ActorDep):
    """SSE stream cho một trạm. Push khi hàng đợi hoặc lệnh tại trạm thay đổi.

    Kết nối sẽ giữ cho đến khi client ngắt hoặc server shutdown.
    Mỗi 15s gửi keepalive để proxy/load balancer không timeout.

    Phiên CSDL mà `ActorDep` mượn được trả lại pool ngay sau khi đọc xong
    (`deps.current_actor` tự đóng giao dịch chỉ-đọc), nên một kết nối mở cả ca không
    giữ kết nối CSDL nào.
    """
    if station not in STEP_NAMES:
        raise Invalid(f"Trạm {station} không hợp lệ")
    actor.require_step(station, VIEW)

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
