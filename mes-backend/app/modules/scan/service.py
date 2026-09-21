"""Quét mã — MỘT cửa vào cho cả sáu trạm.

    ScanResult                             ok · mo_code · station · round_no · duplicate
    scan(db, raw, station, actor_id)       đọc mã → chống trùng → khoá vòng → mở bước

Bốn việc nối tiếp trong một transaction. Chống trùng trả lại NGUYÊN VĂN câu lần trước
kèm cờ `duplicate` — người ở trạm thấy "đã nhận rồi", không thấy báo lỗi.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.common.config import settings
from app.common.errors import Invalid, NotFound
from app.common.uow import transactional
from app.common.vocab.enums import QUEUE_WAITS_ON_PREV_STEP, STEP_NAMES
from app.common.vocab.error_codes import Err
from app.modules.mo import repository as mo_repo
from app.modules.round import repository as round_repo
from app.modules.round import step_service as step_service
from app.modules.scan import repository as scan_repo
from app.modules.scan.mocode import read_mo_code
from app.common.event_bus import mark_affected


@dataclass(frozen=True)
class ScanResult:
    """Kết quả một lần quét. `duplicate` = bắn trùng, KHÔNG phải lỗi."""
    ok: bool
    mo_code: str
    station: int
    message: str
    round_no: int
    duplicate: bool = False


@transactional
def scan(db: Session, *, raw: str, station: int, actor_id: uuid.UUID) -> ScanResult:
    """Đọc mã → chống bắn trùng → khoá vòng → mở bước của trạm đang quét."""
    if station not in STEP_NAMES:
        raise Invalid(f"Trạm {station} không hợp lệ")

    read = read_mo_code(raw)
    if read.code is None:
        raise Invalid(read.error or "Không đọc được mã", code=Err.SCAN_READ)

    mo = mo_repo.get_mo_or_none(db, read.code)
    if mo is None:
        raise NotFound(f"Mã {read.code} không có trong hệ thống")

    dup = _seen_recently(db, mo.id, station)
    if dup is not None:
        # Đầu đọc bắn hai lần là chuyện phần cứng. Trả lại ĐÚNG kết quả lần trước,
        # không báo lỗi — người vận hành không làm gì sai cả.
        rnd_no = round_repo.lock_open_round(db, mo.id).round_no
        return ScanResult(True, mo.code, station, dup, rnd_no, duplicate=True)

    rnd = round_repo.lock_open_round(db, mo.id)
    step_service.accept(db, rnd=rnd, step_no=station, actor_id=actor_id)
    msg = f"{mo.code} — {STEP_NAMES[station]} đã nhận (vòng {rnd.round_no})"
    _remember(db, mo.id, station, msg)
    mark_affected(station)
    if station >= 1:
        mark_affected(station - 1)
    if station + 1 in QUEUE_WAITS_ON_PREV_STEP:
        mark_affected(station + 1)
    return ScanResult(True, mo.code, station, msg, rnd.round_no)


def _seen_recently(db: Session, mo_id: uuid.UUID, station: int) -> str | None:
    return scan_repo.scan_seen_recently(db, mo_id, station, settings.scan.dedupe_seconds)


def _remember(db: Session, mo_id: uuid.UUID, station: int, message: str) -> None:
    scan_repo.scan_remember(db, mo_id, station, message)
