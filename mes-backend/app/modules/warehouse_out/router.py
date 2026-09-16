"""Trạm 0 — Kho XUẤT (kho vật tư) bàn giao xuống xưởng. Phòng Kho xuất.

    POST /warehouse-out/{code}/handover    bàn giao một lệnh
    POST /warehouse-out/handover-batch     bàn giao cả lô 10–100 lệnh (§7A)

Chỉ còn MỘT thao tác là bàn giao — bước In phiếu đã bỏ từ BRD v2.18 để Kho bớt
một lần bấm cho mỗi MO.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter

from app.common.deps import ActorDep, DbDep
from app.common.schemas import OkOut
from app.modules.warehouse_out import service as warehouse_out_service

router = APIRouter(tags=["warehouse-out"])


@router.post("/warehouse-out/{code}/handover", response_model=OkOut)
def handover(code: str, db: DbDep, actor: ActorDep) -> OkOut:
    """Kho bàn giao một lệnh xuống xưởng.
    Chưa bàn giao thì Setup không quét nhận được (§3.2)."""
    actor.require_step(0)
    warehouse_out_service.handover(db, code=code, actor_id=uuid.UUID(actor.user_id))
    return OkOut(message=f"{code} đã bàn giao — Setup nhận được rồi")


@router.post("/warehouse-out/handover-batch", response_model=OkOut)
def handover_batch(codes: list[str], db: DbDep, actor: ActorDep) -> OkOut:
    """Bàn giao NHIỀU lệnh cùng lúc — Kho phải xử 10–100 lệnh một ca (§7A).
    Một mã hỏng thì cả lô không lệnh nào được bàn giao."""
    actor.require_step(0)
    n = warehouse_out_service.handover_batch(db, codes=codes, actor_id=uuid.UUID(actor.user_id))
    return OkOut(message=f"Đã bàn giao {n} lệnh")
