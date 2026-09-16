"""Đóng thùng — chạy SONG SONG với Sản xuất, không phải bước nối tiếp.

Thuộc phòng Sản xuất, nằm TRONG trạm 4 — nên Bàn team leader cũng đóng thùng được (§9b.4).

    POST /packing/{code}/start         bắt đầu, cần ít nhất một chuyền đã chạy
    POST /packing/{code}/hourly        ghi số THÙNG ĐẦY của một khung giờ (§7b.2)
    POST /packing/{code}/finish        kết thúc + ghi SL đã đóng, tính bằng PCS

`qty_packed` mới là con số đẩy tiến độ MO, không phải `qty_ok` của Sản xuất: hàng
đạt mà chưa đóng thùng thì chưa tính (§6b.2).
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter

from app.common.deps import ActorDep, DbDep
from app.common.schemas import OkOut
from app.modules.packing import hourly_service as packing_hourly_service
from app.modules.packing import service as packing_service
from app.modules.packing.schemas import PackingFinishIn, PackingHourlyIn, PackingHourlyOut

router = APIRouter(tags=["packing"])


@router.post("/packing/{code}/start", response_model=OkOut)
def packing_start(code: str, db: DbDep, actor: ActorDep) -> OkOut:
    """Bắt đầu đóng thùng — SONG SONG với sản xuất.
    Cần ít nhất một chuyền đã vào Đang lắp ráp."""
    actor.require_step(4)
    packing_service.packing_start(db, code=code, actor_id=uuid.UUID(actor.user_id))
    return OkOut(message=f"{code} — bắt đầu đóng thùng (song song với SX)")


@router.post("/packing/{code}/hourly", response_model=PackingHourlyOut)
def packing_hourly(code: str, body: PackingHourlyIn, db: DbDep,
                   actor: ActorDep) -> PackingHourlyOut:
    """Ghi số THÙNG ĐẦY của một khung giờ.

    Trả kèm `le_pcs` — hàng đã làm ra nhưng chưa đủ một thùng. Đó **không phải hàng
    thiếu**: thiếu là chưa làm ra được và phải làm thêm; lẻ thì giờ sau gom tiếp, và
    cuối vòng vào thùng lẻ (thùng cuối của đơn được đóng thiếu, §7b.2).
    """
    actor.require_step(4)
    t = packing_hourly_service.add_packing_hourly(
        db, code=code, work_date=body.work_date, slot_hour=body.slot_hour,
        boxes=body.boxes, note=body.note, actor_id=uuid.UUID(actor.user_id),
    )
    return PackingHourlyOut(
        boxes=t.boxes, pcs_per_box=t.pcs_per_box, packed_pcs=t.packed_pcs,
        made_pcs=t.made_pcs, le_pcs=t.le_pcs,
        message=f"Khung {body.slot_hour:02d}h — {t.boxes} thùng × {t.pcs_per_box} "
                f"= {t.boxes * t.pcs_per_box} pcs"
                + (f" · còn lẻ {t.le_pcs} trên bàn (chưa đủ thùng, KHÔNG phải hàng thiếu)"
                   if t.le_pcs else " · không còn hàng lẻ"),
    )


@router.post("/packing/{code}/finish", response_model=OkOut)
def packing_finish(code: str, body: PackingFinishIn, db: DbDep, actor: ActorDep) -> OkOut:
    """Kết thúc đóng thùng, ghi SL đã đóng.
    Đây mới là con số đẩy tiến độ MO, không phải SL đạt."""
    actor.require_step(4)
    packing_service.packing_finish(db, code=code, qty_packed=body.qty_packed,
                                   note_text=body.note_text,
                                   actor_id=uuid.UUID(actor.user_id))
    return OkOut(message=f"{code} — kết thúc đóng thùng {body.qty_packed}")
