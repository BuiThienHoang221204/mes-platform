"""Một chỗ duy nhất lấy giờ. Ba hàm, ba nguồn khác nhau — chọn nhầm là sai lặng lẽ.

    now()            giờ của MÁY CHẠY PYTHON — chỉ để so sánh trong bộ nhớ
    db_now(db)       giờ BẮT ĐẦU GIAO DỊCH, lấy từ CSDL
    db_clock(db)     giờ THẬT ngay lúc gọi, lấy từ CSDL

Nguyên tắc ③: mốc giờ ghi vào CSDL phải do **CSDL** sinh, không lấy từ máy ứng dụng.
Đồng hồ các máy lệch nhau thì `submitted_at` không so được với `mo_step.opened_at`
nữa — mà cả hệ này sống bằng cách trừ hai mốc thời gian.

Vì sao cần cả `db_now` lẫn `db_clock`:

    now()            KHÔNG đổi trong suốt một giao dịch
    clock_timestamp() đổi theo từng lời gọi

Đoạn chuyền có `CHECK seg_ends_after_start` đòi `ended_at > started_at`. Mở rồi đóng
một đoạn trong CÙNG một giao dịch mà dùng `db_now` thì hai mốc BẰNG NHAU và ràng buộc
nổ — lỗi thật đã gặp lúc dựng dự án. Nên đoạn chuyền dùng `db_clock`, còn bước và vòng
dùng `db_now`.
"""

from __future__ import annotations

from datetime import UTC, datetime, timezone
from typing import Optional
from zoneinfo import ZoneInfo

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.common.config import settings

factory_tz = ZoneInfo(settings.tz)


def local_dt(dt: Optional[datetime]) -> Optional[datetime]:
    """Chuyển UTC datetime sang giờ xưởng, giữ tzinfo."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(factory_tz)


def now() -> datetime:
    """Giờ của máy chạy Python. KHÔNG dùng cho cột `_at` — xem đầu file."""
    return datetime.now(UTC)


def db_now(db: Session) -> datetime:
    """Giờ bắt đầu giao dịch, lấy từ CSDL. Không đổi trong suốt giao dịch."""
    return db.scalar(text("SELECT now()"))


def db_clock(db: Session) -> datetime:
    """Giờ thật ngay lúc gọi, lấy từ CSDL. Hai lời gọi liền nhau ra hai giá trị.

    Dùng cho đoạn chuyền: mở và đóng trong cùng một giao dịch thì `db_now` cho hai
    mốc bằng nhau, vi phạm `CHECK seg_ends_after_start`.
    """
    return db.scalar(text("SELECT clock_timestamp()"))
