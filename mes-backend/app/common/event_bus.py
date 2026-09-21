"""In-process event bus — push thay đổi từ backend đến SSE clients.

Mỗi SSE client subscribes theo `station` topic. Khi có ghi ở trạm nào,
bus push sự kiện đến TẤT CẢ client đang nghe trạm đó.

Scale lên multi-worker: thay implementation bằng Redis Pub/Sub,
giữ nguyên interface `subscribe` / `emit`.

═══ Flux ═══════════════════════════════════════════════════════════════════

    Service (trong @transactional)
        │
        ▼
    mark_affected(station)     ──  đánh dấu trạm bị ảnh hưởng
        │
    … commit …
        │
        ▼
    flush_affected()           ──  gọi SAU read_cache.bump() trong uow.py
        │
        ▼
    bus.emit(f"station:{n}", {"type": "changed"})
        │
        ▼
    SSE clients đang nghe trạm n  →  invalidate React Query  →  refetch
"""

from __future__ import annotations

import asyncio
import threading
from collections import defaultdict
from collections.abc import Callable
from contextvars import ContextVar
from typing import Any

# ══ EventBus ═══════════════════════════════════════════════════════════════

_lock = threading.Lock()
_subscribers: dict[str, list[Callable[[dict[str, Any]], None]]] = defaultdict(list)


def subscribe(topic: str, callback: Callable[[dict[str, Any]], None]) -> Callable[[], None]:
    """Đăng ký listener. Trả về hàm unsubscribe."""
    with _lock:
        _subscribers[topic].append(callback)

    def unsub() -> None:
        with _lock:
            try:
                _subscribers[topic].remove(callback)
            except ValueError:
                pass

    return unsub


def emit(topic: str, data: dict[str, Any]) -> None:
    """Push event đến mọi listener của topic."""
    with _lock:
        listeners = list(_subscribers.get(topic, []))
    for cb in listeners:
        try:
            cb(data)
        except Exception:
            pass  # Client disconnect — bỏ qua


# ══ Pending stations (ContextVar) ══════════════════════════════════════════

# Mỗi service gọi `mark_affected(station)` để đánh dấu trạm bị ảnh hưởng
# bởi giao dịch đang chạy. Sau commit, `flush_affected()` push event.

_pending: ContextVar[frozenset[int] | None] = ContextVar("pending_stations", default=None)
"""Mặc định là None, KHÔNG phải một `set()`.

Mặc định của `ContextVar` là MỘT vật thể dùng chung cho mọi context. Để `set()` ở đó
thì một giao dịch lỗi giữa chừng — đánh dấu xong nhưng chưa kịp đẩy — làm bẩn vật thể
ấy vĩnh viễn, và mọi request sau đó khởi đầu với trạm thừa trong tay.
"""


def mark_affected(*stations: int) -> None:
    """Đánh dấu trạm bị ảnh hưởng bởi giao dịch hiện tại."""
    _pending.set(frozenset(_pending.get() or ()) | {s for s in stations if s >= 0})


def flush_affected() -> None:
    """Push event đến tất cả trạm bị ảnh hưởng. Gọi SAU commit + cache bump."""
    pending = _pending.get() or frozenset()
    _pending.set(None)
    for station in sorted(pending):
        emit(f"station:{station}", {"type": "changed", "station": station})


# ══ Cầu sang event loop ════════════════════════════════════════════════════

# Endpoint SSE là `async def` nên chạy TRÊN event loop; endpoint ghi là `def`
# thường nên FastAPI chạy chúng trong threadpool, NGOÀI event loop.


def subscribe_async(topic: str, queue: asyncio.Queue) -> Callable[[], None]:
    """Đăng ký một hàng đợi asyncio. Trả về hàm thôi nghe.

    Vòng lặp phải bắt NGAY ĐÂY, lúc đăng ký. Tra nó lúc phát thì hỏng: `emit` gọi
    từ luồng threadpool của endpoint ghi, ở đó `get_running_loop()` ném lỗi và mọi
    event rơi vào im lặng. Xem `docs/RA-SOAT-POLLING.md` §2/A5.
    """
    loop = asyncio.get_running_loop()

    def _bridge(data: dict[str, Any]) -> None:
        if loop.is_closed():
            return
        try:
            loop.call_soon_threadsafe(_enqueue, queue, data)
        except RuntimeError:
            pass

    return subscribe(topic, _bridge)


def _enqueue(queue: asyncio.Queue, data: dict[str, Any]) -> None:
    """Hàng đầy thì BỎ event, không chặn.

    Chặn ở đây là chặn event loop vì một client đọc chậm. Client đó nối lại sẽ nạp
    lại toàn bộ (`useSSE.onReconnect`), nên mất một event không để lại hậu quả lâu dài.
    """
    try:
        queue.put_nowait(data)
    except asyncio.QueueFull:
        pass
