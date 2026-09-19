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

_pending: ContextVar[set[int]] = ContextVar("pending_stations", default=set())


def mark_affected(*stations: int) -> None:
    """Đánh dấu trạm bị ảnh hưởng bởi giao dịch hiện tại."""
    current = _pending.get()
    for s in stations:
        if s >= 0:
            current.add(s)
    _pending.set(current)


def flush_affected() -> None:
    """Push event đến tất cả trạm bị ảnh hưởng. Gọi SAU commit + cache bump."""
    pending = _pending.get()
    _pending.set(set())
    for station in pending:
        emit(f"station:{station}", {"type": "changed", "station": station})


# ══ Async bridge ═══════════════════════════════════════════════════════════

# SSE endpoint chạy trong async context, nhưng EventBus emit từ sync context.
# Dùng asyncio.Queue để bridge.

_async_queues: dict[str, list[asyncio.Queue]] = defaultdict(list)
_async_lock = asyncio.Lock()


def _sync_to_async_bridge(topic: str, data: dict[str, Any]) -> None:
    """Gọi từ sync emit — đẩy data vào asyncio queues của topic."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return
    if loop.is_closed():
        return

    async def _push() -> None:
        async with _async_lock:
            queues = list(_async_queues.get(topic, []))
        for q in queues:
            try:
                q.put_nowait(data)
            except asyncio.QueueFull:
                pass

    loop.call_soon_threadsafe(asyncio.ensure_future, _push())


def subscribe_async(topic: str, queue: asyncio.Queue) -> Callable[[], None]:
    """Đăng ký async listener. Trả về hàm unsubscribe."""
    async def _bridge(data: dict[str, Any]) -> None:
        try:
            queue.put_nowait(data)
        except asyncio.QueueFull:
            pass

    # Wrap async callback into sync for EventBus
    def _sync_bridge(data: dict[str, Any]) -> None:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return
        if loop.is_closed():
            return
        loop.call_soon_threadsafe(queue.put_nowait, data)

    return subscribe(topic, _sync_bridge)
