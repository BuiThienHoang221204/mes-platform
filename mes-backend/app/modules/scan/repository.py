"""Truy vấn bảng hạ tầng `scan_dedupe` — chống đầu đọc bắn trùng.

    scan_seen_recently(db, mo_id, station, within_sec)   → câu trả lời lần trước
    scan_remember(db, mo_id, station, message)           ghi đè, không đẻ dòng mới

Khoá theo (MÃ, TRẠM) chứ không chỉ theo mã: cùng một MO quét tiếp ở trạm kế bên
phải ăn ngay. `now()` lấy từ DB để lúc ghi và lúc so dùng chung một đồng hồ.
"""

from __future__ import annotations

import uuid

from sqlalchemy import text
from sqlalchemy.orm import Session


def scan_seen_recently(db: Session, mo_id: uuid.UUID, station: int,
                       within_sec: float) -> str | None:
    """Trả lại NGUYÊN VĂN câu trả lời lần trước, hoặc None nếu đã quá cửa sổ.

    `within_sec` là SỐ THỰC, khớp `MES_SCAN_DEDUPE_SECONDS` — cửa sổ chống bắn trùng
    chỉnh được xuống 1.5s hay 0.8s tuỳ đầu đọc. `make_interval(secs => …)` của Postgres
    nhận số thực, nên không phải làm tròn.
    """
    return db.execute(
        text(
            """
            SELECT result_message
            FROM scan_dedupe
            WHERE mo_id = :m AND station_no = :s
              AND scanned_at > now() - make_interval(secs => :w)
            """
        ),
        {"m": mo_id, "s": station, "w": within_sec},
    ).scalar()


def scan_remember(db: Session, mo_id: uuid.UUID, station: int, message: str) -> None:
    """Một dòng cho mỗi (MO, trạm) — quét lại thì ĐÈ lên, không đẻ thêm dòng."""
    db.execute(
        text(
            """
            INSERT INTO scan_dedupe (mo_id, station_no, scanned_at, result_message)
            VALUES (:m, :s, now(), :msg)
            ON CONFLICT (mo_id, station_no)
            DO UPDATE SET scanned_at = now(), result_message = EXCLUDED.result_message
            """
        ),
        {"m": mo_id, "s": station, "msg": message},
    )
