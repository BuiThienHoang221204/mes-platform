"""Cache đọc cho các bảng dùng CHUNG — tách tải CSDL khỏi số máy đang mở.

Bốn endpoint `/board/*` trả về **cùng một dữ liệu cho mọi người**: hàng đợi trạm 2
của ai cũng giống nhau, không cá nhân hoá gì. Vậy 50 máy tính bảng cùng hỏi thì
không có lý do gì chạy 50 lượt truy vấn.

    Không cache:   50 máy × 3 endpoint ÷ 10 giây  →  15 truy vấn/giây
    Có cache:      3 endpoint ÷ 5 giây            →  0,6 truy vấn/giây

Tải CSDL từ đó **không còn phụ thuộc số máy** — thêm 500 máy nữa cũng không đổi.

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

_lock = threading.Lock()
_version = 0
_store: dict[str, tuple[int, float, Any]] = {}


def bump() -> None:
    """Có thao tác ghi — mọi mục cache đang giữ thành cũ."""
    global _version
    with _lock:
        _version += 1


def clear() -> None:
    """Dọn sạch. Dùng trong test để mỗi ca chạy bắt đầu từ bảng trắng."""
    global _version
    with _lock:
        _version += 1
        _store.clear()


def cached(key: str, produce: Callable[[], Any], ttl: float = TTL_SECONDS) -> Any:
    """Trả kết quả của `produce()`, dùng lại nếu vừa chạy và chưa ai ghi gì."""
    now = time.monotonic()
    hit = _store.get(key)
    if hit is not None and hit[0] == _version and hit[1] > now:
        return hit[2]

    version_at_read = _version
    value = produce()
    _store[key] = (version_at_read, now + ttl, value)
    return value
