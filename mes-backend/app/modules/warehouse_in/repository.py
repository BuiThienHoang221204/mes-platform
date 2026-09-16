"""Truy vấn sổ trạm 5 — `warehouse_in`.

    get_warehouse_in(db, round_id)              None = chưa nhập kho

Có dòng nghĩa là vòng này đã nhập kho xong, không nhận lần hai.
"""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.modules.warehouse_in.models import WarehouseIn


def save_warehouse_in(db: Session, round_id: uuid.UUID, *, qty_received: int | None,
                 counted_at, by: uuid.UUID) -> WarehouseIn:
    """Ghi dòng nhập kho. Kho không đếm lại thì `qty_received` rỗng và không có mốc đếm."""
    row = WarehouseIn(
        round_id=round_id, qty_received=qty_received,
        counted_at=counted_at if qty_received is not None else None,
        counted_by=by if qty_received is not None else None,
    )
    db.add(row)
    return row


def get_warehouse_in(db: Session, round_id: uuid.UUID) -> WarehouseIn | None:
    """Sổ nhập kho của một vòng. Có dòng = đã nhập, không nhận lần hai."""
    return db.get(WarehouseIn, round_id)
