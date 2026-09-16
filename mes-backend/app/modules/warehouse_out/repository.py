"""Truy vấn sổ trạm 0 — `warehouse_out`.

    get_warehouse_out(db, round_id)            None = chưa bàn giao

`round/step_service.py` gọi hàm này để chặn Setup nhận lệnh khi Kho chưa bàn giao.
"""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.modules.warehouse_out.models import WarehouseOut


def save_handover(db: Session, round_id: uuid.UUID, by: uuid.UUID) -> WarehouseOut:
    """Ghi dòng bàn giao. Có dòng = đã bàn giao — Setup nhìn vào đây để biết."""
    row = WarehouseOut(round_id=round_id, handed_over_by=by)
    db.add(row)
    return row


def get_warehouse_out(db: Session, round_id: uuid.UUID) -> WarehouseOut | None:
    """Sổ bàn giao của một vòng. None = Kho chưa bàn giao, Setup không nhận được."""
    return db.get(WarehouseOut, round_id)
