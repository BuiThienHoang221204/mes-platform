"""Chặn khởi động nếu có người bật nhiều tiến trình trước khi hạ tầng sẵn sàng.

`event_bus` và `read_cache` đều giữ trạng thái trong bộ nhớ MỘT tiến trình. Chạy
nhiều tiến trình thì cả hai sai, và sai theo kiểu **không báo gì**: SSE tới nhầm
tiến trình nên màn hình đứng im, cache mỗi tiến trình một bản nên người vừa quét
xong vẫn thấy số cũ.

Thà gãy ngay lúc khởi động. Xem `docs/RA-SOAT-POLLING.md` §2/A1, §2/A2 và §5.4.

Cái này KHÔNG phát hiện được nhiều BẢN SAO (mỗi bản sao là một máy chủ riêng, không
đọc được biến môi trường của nhau). Chừng nào chưa làm §5.4 thì số bản sao phải giữ
bằng 1 — xem ghi chú trong `render.yaml`.
"""

from __future__ import annotations

import os

from app.common.config import settings

WORKER_COUNT_ENV_VARS = ("WEB_CONCURRENCY", "UVICORN_WORKERS", "GUNICORN_WORKERS")


def requested_worker_count() -> int:
    """Số tiến trình mà môi trường đang yêu cầu. Giá trị lạ thì coi như 1."""
    for name in WORKER_COUNT_ENV_VARS:
        value = os.environ.get(name)
        if not value:
            continue
        try:
            return max(1, int(value))
        except ValueError:
            continue
    return 1


def assert_single_process() -> None:
    """Ném `RuntimeError` nếu đang bị bảo chạy nhiều tiến trình mà chưa mở cổng."""
    n = requested_worker_count()
    if n <= 1 or settings.allow_multi_process:
        return

    raise RuntimeError(
        f"\n[khởi động] Đang yêu cầu {n} tiến trình, nhưng bản này chỉ chạy đúng MỘT.\n"
        "  event_bus và read_cache giữ trạng thái trong bộ nhớ một tiến trình:\n"
        "    · SSE đẩy tới nhầm tiến trình  → màn hình trạm đứng im, KHÔNG báo lỗi\n"
        "    · cache mỗi tiến trình một bản → quét xong vẫn thấy số cũ\n"
        f"  Cách sửa: bỏ {'/'.join(WORKER_COUNT_ENV_VARS)} hoặc đặt về 1.\n"
        "  Muốn chạy nhiều tiến trình thật thì làm docs/RA-SOAT-POLLING.md §5.4\n"
        "  (đưa event_bus + read_cache ra chỗ dùng chung) rồi đặt\n"
        "  MES_ALLOW_MULTI_PROCESS=true."
    )
