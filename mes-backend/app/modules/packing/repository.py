"""Truy vấn hai sổ Đóng thùng — `packing` và `packing_hourly`.

    get_packing(db, round_id)              None = chưa bắt đầu đóng thùng
    add_packing_hourly(db, ...)            ghi số THÙNG ĐẦY của một khung giờ
    packing_hourly_of(db, round_id)        mọi khung giờ đã ghi thùng của vòng
    packing_hourly_of_rounds(db, ids)      bản theo LÔ — dùng cho màn truy vết
    packed_boxes_pcs(db, round_id)         Σ thùng × quy cách, quy ra PCS

PK chính là `round_id` nên `db.get` là đủ, không cần câu SELECT. **Có dòng nghĩa
là đã bắt đầu** — không có cột "đã đóng thùng chưa".
"""

from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.packing.models import Packing, PackingHourly


def save_packing(db: Session, round_id: uuid.UUID, by: uuid.UUID) -> Packing:
    """Mở sổ đóng thùng. Kết thúc thì service sửa thẳng `qty_packed` trên dòng này."""
    row = Packing(round_id=round_id, started_by=by)
    db.add(row)
    return row


def get_packing(db: Session, round_id: uuid.UUID) -> Packing | None:
    """Sổ đóng thùng của một vòng. None = chưa bắt đầu đóng thùng."""
    return db.get(Packing, round_id)


def packing_of_rounds(db: Session, round_ids: list[uuid.UUID]) -> dict[uuid.UUID, Packing]:
    """Bản theo lô của `get_packing`. Vòng chưa đóng thùng thì thiếu khoá."""
    if not round_ids:
        return {}
    rows = db.scalars(select(Packing).where(Packing.round_id.in_(round_ids)))
    return {p.round_id: p for p in rows}


def add_packing_hourly(db: Session, *, round_id: uuid.UUID, work_date: date, slot_hour: int,
                       boxes: int, pcs_per_box: int, note: str | None,
                       by: uuid.UUID) -> PackingHourly:
    """Ghi số THÙNG ĐẦY của một khung giờ.

    `pcs_per_box` chép vào dòng chứ không đọc sang MO lúc đọc lại — quy cách bị sửa
    một lần là mọi dòng cũ quy ra số pcs khác.

    Trùng (vòng, ngày, khung giờ) thì UNIQUE ở DB chặn; đóng nhiều hơn số đã làm ra
    thì trigger `packing_hourly_within_made` chặn. Cả hai nổ lúc flush.
    """
    row = PackingHourly(round_id=round_id, work_date=work_date, slot_hour=slot_hour,
                        boxes=boxes, pcs_per_box=pcs_per_box, note=note, recorded_by=by)
    db.add(row)
    db.flush()
    return row


def packing_hourly_of(db: Session, round_id: uuid.UUID) -> list[PackingHourly]:
    """Mọi khung giờ đã ghi thùng của vòng, xếp theo ngày rồi khung giờ."""
    return list(db.scalars(
        select(PackingHourly).where(PackingHourly.round_id == round_id)
        .order_by(PackingHourly.work_date, PackingHourly.slot_hour)
    ))


def packed_boxes_pcs(db: Session, round_id: uuid.UUID) -> int:
    """Σ(thùng × quy cách) của vòng, quy ra PCS. Chưa ghi dòng nào thì 0.

    Cộng ở CSDL chứ không kéo hết dòng về rồi cộng bằng Python: con số này chỉ dùng
    để hiện "đã đóng bao nhiêu", không cần từng dòng.
    """
    return db.scalar(
        select(func.coalesce(func.sum(PackingHourly.boxes * PackingHourly.pcs_per_box), 0))
        .where(PackingHourly.round_id == round_id)
    ) or 0


def packing_hourly_of_rounds(
    db: Session, round_ids: list[uuid.UUID]
) -> dict[uuid.UUID, list[PackingHourly]]:
    """Bản theo lô của `packing_hourly_of`.

    Màn truy vết vẽ mọi vòng cùng lúc; gọi từng vòng một là N+1 — xem
    `steps_of_rounds` để biết vì sao dự án này canh chuyện đó.
    """
    if not round_ids:
        return {}
    rows = db.scalars(
        select(PackingHourly).where(PackingHourly.round_id.in_(round_ids))
        .order_by(PackingHourly.round_id, PackingHourly.work_date, PackingHourly.slot_hour)
    )
    by_round: dict[uuid.UUID, list[PackingHourly]] = defaultdict(list)
    for r in rows:
        by_round[r.round_id].append(r)
    return dict(by_round)
