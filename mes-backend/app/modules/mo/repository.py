"""Truy vấn bảng `manufacturing_order`.

    get_mo(db, code)                       NÉM lỗi nếu không có
    list_mos(db, status=None)              danh sách lệnh, mới nhất trước
    get_mo_or_none(db, code)               trả None nếu không có

`get_mo` dùng ở đường đi chính nơi thiếu MO là sai; `get_mo_or_none` dùng khi
đang KIỂM xem mã đã tồn tại chưa.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.errors import NotFound
from app.common.vocab.enums import MoStatus
from app.modules.mo.models import ManufacturingOrder


def save_mo(db: Session, *, code: str, product_name: str, quantity: int,
            required_production_sec: int, pcs_per_box: int, by: uuid.UUID) -> ManufacturingOrder:
    """Ghi một lệnh mới, trạng thái DRAFT. `UNIQUE (code)` chặn trùng mã lúc flush."""
    mo = ManufacturingOrder(
        code=code, product_name=product_name, quantity=quantity,
        required_production_sec=required_production_sec, pcs_per_box=pcs_per_box,
        created_by=by,
    )
    db.add(mo)
    return mo


def get_mo(db: Session, code: str) -> ManufacturingOrder:
    """Không có thì NÉM lỗi — dùng ở đường đi chính, nơi thiếu MO là sai."""
    mo = db.scalar(select(ManufacturingOrder).where(ManufacturingOrder.code == code))
    if mo is None:
        raise NotFound(f"Không có MO {code} trong hệ thống")
    return mo


def get_mo_or_none(db: Session, code: str) -> ManufacturingOrder | None:
    """Không có thì trả None — dùng khi đang KIỂM xem mã đã tồn tại chưa."""
    return db.scalar(select(ManufacturingOrder).where(ManufacturingOrder.code == code))


def list_mos(db: Session, *, status: MoStatus | None = None,
             limit: int = 200) -> list[ManufacturingOrder]:
    """Danh sách lệnh, mới tạo trước.

    Màn Kế hoạch cần cái này: lệnh vừa tạo ở trạng thái DRAFT không nằm trong
    hàng đợi trạm nào cả, nên không có đường nào khác để tìm lại nó.

    Có `limit` cứng vì bảng này chỉ lớn lên: xưởng chạy vài năm là vài chục nghìn
    dòng, trả hết về là treo màn hình.
    """
    stmt = select(ManufacturingOrder)
    if status is not None:
        stmt = stmt.where(ManufacturingOrder.status == status)
    return list(db.scalars(
        stmt.order_by(ManufacturingOrder.created_at.desc()).limit(limit)
    ))
