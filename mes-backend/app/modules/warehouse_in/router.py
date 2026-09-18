"""Trạm 5 — Kho NHẬP (kho thành phẩm). Nơi MO đóng lại HOẶC chạy tiếp.

Phòng Kho nhập — KHÁC phòng Kho xuất ở trạm 0: người giao vật tư không được tự
nhận thành phẩm của chính lô mình giao (§9b.1).

    POST /warehouse-in/{code}/complete      nhận hàng về kho — không có body

Một endpoint, hai kết cục: đủ SL → COMPLETED; thiếu → server mở vòng mới ngay
trong cùng transaction. FE phải phân nhánh theo `outcome`.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter

from app.common.deps import ActorDep, DbDep
from app.modules.warehouse_in import service as warehouse_in_service
from app.modules.warehouse_in.schemas import WarehouseInCompleteOut

router = APIRouter(tags=["warehouse-in"])


@router.post("/warehouse-in/{code}/complete", response_model=WarehouseInCompleteOut)
def complete(code: str, db: DbDep, actor: ActorDep) -> WarehouseInCompleteOut:
    """Nhập kho — đủ SL thì MO COMPLETED, thiếu thì tự mở vòng mới về Bàn team leader.

    Không nhận số liệu nào từ client: số nhập kho **là** số đã đóng thùng (§8).
    FE phải phân nhánh theo `outcome`."""
    actor.require_step(5)
    out = warehouse_in_service.complete(
        db, code=code, actor_id=uuid.UUID(actor.user_id))
    msg = (f"{code} HOÀN THÀNH — đủ {out.qty_done}" if out.outcome == "COMPLETED"
           else f"{code} còn {out.qty_remain} — về Bàn team leader, mở vòng {out.new_round_no}")
    return WarehouseInCompleteOut(outcome=out.outcome, qty_done=out.qty_done,
                        qty_remain=out.qty_remain, new_round_no=out.new_round_no, message=msg)
