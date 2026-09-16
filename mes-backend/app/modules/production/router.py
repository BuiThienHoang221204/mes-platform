"""Trạm 4 — Sản xuất. Phòng Sản xuất (và Bàn team leader, §9b.4). Gồm cả ô ghi sản lượng giờ.

    POST /lines/{code}/assign          thêm chuyền → TG chờ bắt đầu đếm
    POST /lines/{code}/start           cho chạy    → TG thực tế bắt đầu đếm
    POST /lines/{code}/hold            dừng máy    → bắt buộc ghi lý do (§17)
    POST /production/{code}/close      chốt sổ: đạt + hỏng + thiếu = mục tiêu vòng
    POST /hourly/{code}                ghi sản lượng một khung giờ — BA số (§7.2b)

Ba thao tác đầu ghi vào `line_segment`; chốt sổ ghi vào `production` và đóng mọi
chuyền còn mở cùng một mốc giờ (§16).
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter

from app.common.deps import ActorDep, DbDep
from app.common.schemas import OkOut
from app.modules.production import hourly_service as hourly_service
from app.modules.production import service as production_service
from app.modules.production.schemas import (
    HourlyIn,
    LineAssignIn,
    LineHoldIn,
    LineStartIn,
    ProductionCloseIn,
)

router = APIRouter(tags=["production"])


@router.post("/lines/{code}/assign", response_model=OkOut)
def assign_line(code: str, body: LineAssignIn, db: DbDep, actor: ActorDep) -> OkOut:
    """Thêm chuyền vào vòng đang chạy. TG CHỜ của chuyền bắt đầu đếm từ đây."""
    actor.require_step(4)
    production_service.assign_line(db, code=code, line_code=body.line_code,
                                   actor_id=uuid.UUID(actor.user_id))
    return OkOut(message=f"Đã thêm {body.line_code} — TG chờ bắt đầu chạy")


@router.post("/lines/{code}/start", response_model=OkOut)
def start_line(code: str, body: LineStartIn, db: DbDep, actor: ActorDep) -> OkOut:
    """Cho chuyền chạy. TG chờ chốt lại, TG THỰC TẾ bắt đầu đếm."""
    actor.require_step(4)
    production_service.line_start(db, code=code, line_code=body.line_code,
                                  actor_id=uuid.UUID(actor.user_id))
    return OkOut(message=f"{body.line_code} đang lắp ráp — TG thực tế bắt đầu đếm")


@router.post("/lines/{code}/hold", response_model=OkOut)
def hold_line(code: str, body: LineHoldIn, db: DbDep, actor: ActorDep) -> OkOut:
    """Dừng chuyền, BẮT BUỘC ghi lý do (§17).
    TG thực tế đứng lại, TG chờ chạy tiếp."""
    actor.require_step(4)
    production_service.line_hold(db, code=code, line_code=body.line_code,
                                 reason_code_id=body.reason_code_id,
                                 reason_text=body.reason_text,
                                 actor_id=uuid.UUID(actor.user_id))
    return OkOut(message=f"{body.line_code} đã dừng — TG thực tế đứng lại, TG chờ chạy tiếp")


@router.post("/production/{code}/close", response_model=OkOut)
def close_production(code: str, body: ProductionCloseIn, db: DbDep,
                     actor: ActorDep) -> OkOut:
    """Chốt sổ SX: đạt + hỏng + thiếu cộng ĐÚNG BẰNG mục tiêu vòng.
    Đóng luôn mọi chuyền còn mở, tất cả cùng một mốc giờ (§16)."""
    actor.require_step(4)
    production_service.close_production(
        db, code=code, qty_ok=body.qty_ok, qty_ng=body.qty_ng, qty_short=body.qty_short,
        ng_reason_code_id=body.ng_reason_code_id, ng_reason_text=body.ng_reason_text,
        short_reason_code_id=body.short_reason_code_id,
        short_reason_text=body.short_reason_text, actor_id=uuid.UUID(actor.user_id),
    )
    return OkOut(
        message=f"Chốt sổ SX — đạt {body.qty_ok} · hỏng {body.qty_ng} · thiếu {body.qty_short}"
    )


@router.post("/hourly/{code}", response_model=OkOut)
def add_hourly(code: str, body: HourlyIn, db: DbDep, actor: ActorDep) -> OkOut:
    """Ghi sản lượng MỘT khung giờ, chỉ khi đang có chuyền chạy.
    Mỗi (vòng, ngày, khung giờ) một dòng."""
    actor.require_step(4)
    hourly_service.add_hourly(db, code=code, work_date=body.work_date,
                              slot_hour=body.slot_hour, headcount=body.headcount,
                              target_qty=body.target_qty, qty=body.qty, note=body.note,
                              actor_id=uuid.UUID(actor.user_id))
    return OkOut(message=f"Khung {body.slot_hour:02d}h — thực tế {body.qty}"
                         f"/yêu cầu {body.target_qty} · {body.headcount} người")
