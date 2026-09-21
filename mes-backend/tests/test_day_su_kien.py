"""Đường ĐẨY — từ lúc service ghi xong tới lúc SSE client nhận được.

Hai ca đầu canh đúng chỗ đã hỏng: cả hai đều là lỗi IM LẶNG, không ném gì, không
ghi log, chỉ là màn hình ngoài xưởng không đổi. Xem `docs/RA-SOAT-POLLING.md` §2/A5.
"""

from __future__ import annotations

import asyncio
import contextvars

from app.common import event_bus


def test_ghi_tu_luong_threadpool_van_toi_duoc_SSE():
    """Endpoint ghi là `def` thường nên FastAPI chạy nó NGOÀI event loop.

    Bắt vòng lặp lúc phát thay vì lúc đăng ký là mọi event rơi vào im lặng — SSE
    trông như đang chạy, kết nối vẫn mở, keepalive vẫn về, mà không bao giờ có tin.
    """

    async def scenario():
        queue = asyncio.Queue(maxsize=8)
        stop_listening = event_bus.subscribe_async("station:2", queue)
        try:
            await asyncio.to_thread(
                event_bus.emit, "station:2", {"type": "changed", "station": 2}
            )
            return await asyncio.wait_for(queue.get(), timeout=2)
        finally:
            stop_listening()

    assert asyncio.run(scenario())["station"] == 2


def test_ca_duong_mark_affected_tu_luong_khac():
    """Đúng đường mà `uow.transaction()` đi: đánh dấu rồi đẩy, cả hai ngoài event loop."""

    async def scenario():
        queue = asyncio.Queue(maxsize=8)
        stop_listening = event_bus.subscribe_async("station:4", queue)

        def like_a_transaction():
            event_bus.mark_affected(4)
            event_bus.flush_affected()

        try:
            await asyncio.to_thread(like_a_transaction)
            return await asyncio.wait_for(queue.get(), timeout=2)
        finally:
            stop_listening()

    assert asyncio.run(scenario())["station"] == 4


def test_giao_dich_hong_giua_chung_khong_lam_ban_request_sau():
    """Đánh dấu xong mà chưa kịp đẩy thì KHÔNG được để lại gì cho context sau.

    `ContextVar` dùng CHUNG một vật thể mặc định cho mọi context, nên để `set()` ở đó
    là một lần lỗi làm bẩn vĩnh viễn: mọi request sau đều đẩy thừa trạm đó.
    """
    contextvars.copy_context().run(lambda: event_bus.mark_affected(3))

    def fresh_context():
        return event_bus._pending.get()

    assert not contextvars.copy_context().run(fresh_context)


def test_hang_day_thi_bo_event_chu_khong_lam_hong_luong_ghi():
    """Một client đọc chậm không được phép làm hỏng lượt quét của người khác."""

    async def scenario():
        queue = asyncio.Queue(maxsize=2)
        stop_listening = event_bus.subscribe_async("station:1", queue)
        try:
            for _ in range(10):
                await asyncio.to_thread(
                    event_bus.emit, "station:1", {"type": "changed", "station": 1}
                )
            await asyncio.sleep(0.05)
            return queue.qsize()
        finally:
            stop_listening()

    assert asyncio.run(scenario()) == 2
