"""Truy vấn ba bảng của trạm 4: `production` · `line_segment` · `hourly_output`.

    get_production(db, round_id)                   sổ chốt, None = chưa chốt
    open_segment_of(db, round_id, line_id)         quãng đang mở của MỘT chuyền
    segments_of(db, round_id)                      mọi quãng của vòng
    open_segments_of(db, round_id)                 mọi quãng còn mở — dùng khi chốt sổ
    hourly_of(db, round_id)                        sản lượng từng giờ
    add_hourly(db, ...)                            ghi một khung giờ — BA số (§7.2b)

Hai hàm lấy quãng ĐANG MỞ đều `with_for_update()`: bấm dừng và bấm chạy có thể
tới cùng lúc từ hai máy, không khoá thì một trong hai lệnh mất trắng.
"""

from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.common.vocab.enums import SegmentKind
from app.modules.catalog.models import Line
from app.modules.production.models import HourlyOutput, LineSegment, Production


def save_segment(db: Session, round_id: uuid.UUID, line_id: int, *, kind: SegmentKind,
                 started_at=None, by: uuid.UUID, hold_reason_code_id: int | None = None,
                 hold_reason_text: str | None = None) -> LineSegment:
    """Mở một đoạn chuyền. `started_at` bỏ trống thì để DEFAULT của CSDL lo.

    `kind` WAIT là chờ, RUN là đang lắp ráp. Lý do dừng chỉ gắn với đoạn WAIT —
    `CHECK seg_reason_only_on_wait` canh điều đó.
    """
    seg = LineSegment(round_id=round_id, line_id=line_id, kind=kind, started_by=by,
                      hold_reason_code_id=hold_reason_code_id,
                      hold_reason_text=hold_reason_text)
    if started_at is not None:
        seg.started_at = started_at
    db.add(seg)
    return seg


def save_production(db: Session, round_id: uuid.UUID, *, qty_ok: int, qty_ng: int,
                    qty_short: int, ng_reason_code_id: int | None, ng_reason_text: str | None,
                    short_reason_code_id: int | None, short_reason_text: str | None,
                    by: uuid.UUID) -> Production:
    """Chốt sổ sản xuất. Trigger `production_balances` nổ lúc flush nếu ba số không khớp."""
    row = Production(
        round_id=round_id, qty_ok=qty_ok, qty_ng=qty_ng, qty_short=qty_short,
        ng_reason_code_id=ng_reason_code_id, ng_reason_text=ng_reason_text,
        short_reason_code_id=short_reason_code_id, short_reason_text=short_reason_text,
        closed_by=by,
    )
    db.add(row)
    return row


def get_production(db: Session, round_id: uuid.UUID) -> Production | None:
    """Sổ chốt SX của một vòng. None = chưa chốt sổ."""
    return db.get(Production, round_id)


def open_segment_of(db: Session, round_id: uuid.UUID, line_id: int) -> LineSegment | None:
    """Quãng đang mở của MỘT chuyền trong vòng. Có khoá dòng — hai máy bấm cùng lúc."""
    return db.scalar(
        select(LineSegment).where(
            LineSegment.round_id == round_id,
            LineSegment.line_id == line_id,
            LineSegment.ended_at.is_(None),
        ).with_for_update()
    )


def segments_of(db: Session, round_id: uuid.UUID) -> list[LineSegment]:
    """Mọi quãng của vòng, xếp theo chuyền rồi theo thời gian."""
    return list(db.scalars(
        select(LineSegment).where(LineSegment.round_id == round_id)
        .order_by(LineSegment.line_id, LineSegment.started_at)
    ))


def open_segments_of(db: Session, round_id: uuid.UUID) -> list[LineSegment]:
    """Mọi quãng còn mở của vòng — dùng khi chốt sổ, phải đóng hết chuyền."""
    return list(db.scalars(
        select(LineSegment).where(
            LineSegment.round_id == round_id, LineSegment.ended_at.is_(None)
        ).with_for_update()
    ))


def held_line_codes(db: Session, round_id: uuid.UUID) -> list[str]:
    """Mã những chuyền ĐANG DỪNG của vòng — đoạn WAIT còn mở và có ghi lý do.

    Khác `never_ran`: chuyền dừng đã từng chạy nên có đoạn RUN trong lịch sử, lọt
    qua phép trừ tập hợp. §16 chặn cả hai, nên phải hỏi riêng.
    """
    return list(db.scalars(
        select(Line.code)
        .join(LineSegment, LineSegment.line_id == Line.id)
        .where(
            LineSegment.round_id == round_id,
            LineSegment.ended_at.is_(None),
            LineSegment.kind == SegmentKind.WAIT,
            LineSegment.hold_reason_text.is_not(None),
        )
        .order_by(Line.code)
    ))


def hourly_of(db: Session, round_id: uuid.UUID) -> list[HourlyOutput]:
    """Sản lượng từng giờ của vòng, xếp theo ngày rồi khung giờ."""
    return list(db.scalars(
        select(HourlyOutput).where(HourlyOutput.round_id == round_id)
        .order_by(HourlyOutput.work_date, HourlyOutput.slot_hour)
    ))


def hourly_page(db: Session, round_id: uuid.UUID, *,
                limit: int, offset: int = 0) -> list[HourlyOutput]:
    """MỘT TRANG sản lượng giờ của vòng. Một vòng chạy một tuần là ~56 dòng.

    `(work_date, slot_hour)` đã là duy nhất trong một vòng — chỉ mục duy nhất của
    bảng bảo đảm điều đó — nên cặp này đủ làm khoá sắp ổn định, không cần thêm.
    """
    return list(db.scalars(
        select(HourlyOutput).where(HourlyOutput.round_id == round_id)
        .order_by(HourlyOutput.work_date, HourlyOutput.slot_hour)
        .limit(limit).offset(offset)
    ))


def count_hourly(db: Session, round_id: uuid.UUID) -> int:
    return db.scalar(
        select(func.count()).select_from(HourlyOutput)
        .where(HourlyOutput.round_id == round_id)
    ) or 0


def hourly_of_rounds(
    db: Session, round_ids: list[uuid.UUID]
) -> dict[uuid.UUID, list[HourlyOutput]]:
    """Bản theo lô của `hourly_of` — xem `steps_of_rounds` để biết vì sao cần."""
    if not round_ids:
        return {}
    rows = db.scalars(
        select(HourlyOutput).where(HourlyOutput.round_id.in_(round_ids))
        .order_by(HourlyOutput.round_id, HourlyOutput.work_date, HourlyOutput.slot_hour)
    )
    theo_vong: dict[uuid.UUID, list[HourlyOutput]] = defaultdict(list)
    for h in rows:
        theo_vong[h.round_id].append(h)
    return dict(theo_vong)


def production_of_rounds(
    db: Session, round_ids: list[uuid.UUID]
) -> dict[uuid.UUID, Production]:
    """Bản theo lô của `get_production`. Vòng chưa chốt sổ thì thiếu khoá."""
    if not round_ids:
        return {}
    rows = db.scalars(select(Production).where(Production.round_id.in_(round_ids)))
    return {p.round_id: p for p in rows}


def add_hourly(db: Session, *, round_id: uuid.UUID, work_date: date, slot_hour: int,
               headcount: int, target_qty: int, qty: int, note: str | None,
               by: uuid.UUID) -> HourlyOutput:
    """Trùng (vòng, ngày, khung giờ) thì chỉ mục duy nhất một phần ở DB chặn."""
    row = HourlyOutput(round_id=round_id, work_date=work_date, slot_hour=slot_hour,
                       headcount=headcount, target_qty=target_qty,
                       qty=qty, note=note, recorded_by=by)
    db.add(row)
    db.flush()
    return row
