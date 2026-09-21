"""Quét nhận ở một trạm làm lệnh RƠI VÀO hàng chờ của trạm sau — trạm sau phải được báo.

`mark_affected` là nguồn DUY NHẤT của cả hai đường: SSE đẩy tới tablet, và xoá cache
theo phạm vi. Thiếu một trạm ở đây thì màn hình trạm đó đứng im mà không có lỗi nào
hiện ra — xem `docs/RA-SOAT-POLLING.md` §2/A4.

Danh sách ca sinh từ `QUEUE_WAITS_ON_PREV_STEP`, không gõ tay: thêm một trạm vào tập
đó mà quên báo cho nó thì test này đỏ ngay.
"""

from __future__ import annotations

import uuid
from collections.abc import Callable

import pytest
from sqlalchemy.orm import Session

from app.common import event_bus
from app.common.vocab.enums import QUEUE_WAITS_ON_PREV_STEP
from app.modules.board import repository as board_repo
from app.modules.scan import service as scan_service


def _listen(*stations: int) -> tuple[dict[int, list], Callable[[], None]]:
    received: dict[int, list] = {s: [] for s in stations}
    unsubs = [
        event_bus.subscribe(f"station:{s}", (lambda n: lambda d: received[n].append(d))(s))
        for s in stations
    ]

    def stop_listening() -> None:
        for h in unsubs:
            h()

    return received, stop_listening


def _advance_to_station(flow, code: str, station: int) -> None:
    """Đưa lệnh tới ngay TRƯỚC `tram` — tức đang nằm trong hàng chờ của nó."""
    flow.accept(code, 0)
    flow.handover(code)
    for step in range(1, station):
        flow.accept(code, step)
        if step == 2:
            flow.qc(code, "PASS")


@pytest.mark.parametrize("next_station", sorted(QUEUE_WAITS_ON_PREV_STEP))
def test_quet_nhan_thi_tram_ke_tiep_duoc_bao(
    db: Session, actor: uuid.UUID, make_mo, flow, next_station: int
):
    scan_station = next_station - 1
    code = make_mo()
    _advance_to_station(flow, code, scan_station)

    before = board_repo.count_queue(db, next_station)

    received, stop_listening = _listen(scan_station, next_station)
    try:
        scan_service.scan(db, raw=code, station=scan_station, actor_id=actor)
    finally:
        stop_listening()

    assert board_repo.count_queue(db, next_station) == before + 1, (
        f"quét nhận ở trạm {scan_station} phải đẩy lệnh vào hàng chờ trạm {next_station}"
    )
    assert received[scan_station], f"trạm {scan_station} không nhận được thông báo nào"
    assert received[next_station], (
        f"trạm {next_station} vừa có thêm việc nhưng KHÔNG được báo — "
        f"tablet trạm đó sẽ đứng im cho tới khi có lý do khác nạp lại"
    )


def test_quet_nhan_thi_tram_truoc_cung_duoc_bao(db: Session, actor: uuid.UUID, make_mo, flow):
    """Bước trạm trước ĐÓNG khi trạm sau quét nhận — lệnh rơi khỏi màn hình của họ."""
    code = make_mo()
    _advance_to_station(flow, code, 1)

    received, stop_listening = _listen(0)
    try:
        scan_service.scan(db, raw=code, station=1, actor_id=actor)
    finally:
        stop_listening()

    assert received[0], "trạm 0 vừa mất một lệnh khỏi tay nhưng không được báo"
