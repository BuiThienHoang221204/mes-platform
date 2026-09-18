"""Quét mã QR — MỘT cửa vào cho cả sáu trạm.

    POST /scan                         nhận lệnh tại trạm của thiết bị

Mã QR chỉ nói MO nào, không nói bước nào (§1b.3) — bước suy từ VAI của người quét.
Người vận hành cầm điện thoại đi theo hàng, nên bước không gắn với thiết bị được.
Client khai trạm thì server vẫn kiểm lại bằng `require_station`.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter

from app.common.deps import ActorDep, DbDep
from app.modules.scan import service as scan_service
from app.modules.scan.schemas import ScanIn, ScanOut

router = APIRouter(tags=["scan"])


@router.post("/scan", response_model=ScanOut)
def scan(body: ScanIn, db: DbDep, actor: ActorDep) -> ScanOut:
    """Quét mã QR để NHẬN lệnh — thao tác chung của cả sáu trạm.
    Trạm suy từ vai người quét; bắn trùng trong 2 giây trả lại kết quả lần trước."""
    station = actor.scan_station(body.station)
    actor.require_station(station)
    r = scan_service.scan(db, raw=body.raw, station=station,
                          actor_id=uuid.UUID(actor.user_id))
    return ScanOut(ok=r.ok, mo_code=r.mo_code, station=r.station,
                     round_no=r.round_no, message=r.message, duplicate=r.duplicate)
