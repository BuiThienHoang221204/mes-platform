"""Cache đọc cho các bảng dùng CHUNG — tách tải CSDL khỏi số máy đang mở.

Bốn endpoint `/board/*` trả về **cùng một dữ liệu cho mọi người**: hàng đợi trạm 2
của ai cũng giống nhau, không cá nhân hoá gì. Vậy 50 máy tính bảng cùng hỏi thì
không có lý do gì chạy 50 lượt truy vấn.

    Không cache:   50 máy × 3 endpoint ÷ 10 giây  →  15 truy vấn/giây
    Có cache:      3 endpoint ÷ 5 giây            →  0,6 truy vấn/giây

Tải CSDL từ đó **không còn phụ thuộc số máy** — thêm 500 máy nữa cũng không đổi.

Con số trên chỉ đúng khi cache còn hiệu lực. Nhịp ghi của xưởng, cơ chế chống dồn
và cách đọc `stats()` nằm trong `docs/RA-SOAT-POLLING.md`.

═══ Vì sao bám PHIÊN BẢN chứ không chỉ TTL ═══════════════════════════════════

Chỉ đặt TTL 5 giây thì người vừa quét nhận xong nhìn hàng đợi vẫn thấy lệnh cũ
trong 5 giây nữa — phá đúng thứ `invalidateQueries` bên FE bảo đảm, và người vận
hành sẽ quét lại lần hai vì tưởng máy không ăn.

Nên mỗi lần có thao tác GHI (`@transactional` trong `uow.py`) thì `bump()` nâng số
phiên bản, và mọi mục cache mang phiên bản cũ thành vô hiệu ngay lập tức. TTL chỉ
còn là lưới an toàn cho trường hợp có ai ghi thẳng vào CSDL không qua service.

Đọc phiên bản TRƯỚC khi chạy truy vấn: nếu có người ghi xen vào giữa lúc truy vấn
đang chạy thì mục vừa tạo mang phiên bản cũ và tự hỏng — thà bỏ công một lần còn
hơn phục vụ số cũ mà tưởng là mới.
"""

from __future__ import annotations

import threading
import time
from collections.abc import Callable
from typing import Any

TTL_SECONDS = 5.0
MAX_KEYS = 512
GATE_COUNT = 64

_lock = threading.Lock()
_version = 0
_store: dict[str, tuple[int, float, Any]] = {}
_gates = tuple(threading.Lock() for _ in range(GATE_COUNT))
_hits = 0
_misses = 0
_waits = 0


def bump() -> None:
    """Có thao tác ghi — mọi mục cache đang giữ thành cũ."""
    global _version
    with _lock:
        _version += 1


def clear() -> None:
    """Dọn sạch. Dùng trong test để mỗi ca chạy bắt đầu từ bảng trắng."""
    global _version, _hits, _misses, _waits
    with _lock:
        _version += 1
        _store.clear()
        _hits = 0
        _misses = 0
        _waits = 0


def stats() -> dict[str, Any]:
    """Số liệu để trả lời: cache có thật sự đỡ được gì không."""
    with _lock:
        served = _hits + _misses
        return {
            "hits": _hits,
            "misses": _misses,
            "waits": _waits,
            "served": served,
            "hit_rate": round(_hits / served, 4) if served else None,
            "keys": len(_store),
            "version": _version,
            "ttl_seconds": TTL_SECONDS,
        }


def _fresh(key: str) -> tuple[bool, Any]:
    hit = _store.get(key)
    if hit is not None and hit[0] == _version and hit[1] > time.monotonic():
        return True, hit[2]
    return False, None


def _record(hit: bool, waited: bool) -> None:
    global _hits, _misses, _waits
    with _lock:
        if hit:
            _hits += 1
        else:
            _misses += 1
        if waited:
            _waits += 1


def _remember(key: str, version: int, value: Any, ttl: float) -> None:
    now = time.monotonic()
    with _lock:
        _store[key] = (version, now + ttl, value)
        if len(_store) <= MAX_KEYS:
            return
        for stale in [k for k, v in list(_store.items())
                      if v[1] <= now or v[0] != _version]:
            _store.pop(stale, None)
        if len(_store) > MAX_KEYS:
            _store.clear()


def cached(key: str, produce: Callable[[], Any], ttl: float = TTL_SECONDS) -> Any:
    """Trả kết quả của `produce()`, dùng lại nếu vừa chạy và chưa ai ghi gì.

    Nhiều lượt hỏi CÙNG một key mà cùng trượt thì chỉ MỘT lượt chạy `produce()`,
    các lượt còn lại chờ và dùng chung kết quả đó.
    """
    ok, value = _fresh(key)
    if ok:
        _record(True, False)
        return value

    gate = _gates[hash(key) % GATE_COUNT]
    waited = not gate.acquire(blocking=False)
    if waited:
        gate.acquire()
    try:
        ok, value = _fresh(key)
        if ok:
            _record(True, waited)
            return value

        _record(False, waited)
        version_at_read = _version
        value = produce()
        _remember(key, version_at_read, value, ttl)
        return value
    finally:
        gate.release()
