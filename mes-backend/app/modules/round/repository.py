"""Truy vấn `mo_round` và `mo_step` — TRỤC của cả hệ thống.

    lock_open_round(db, mo_id)             ★ khoá vòng đang mở — chốt chống đua
    progress_row(db, mo_id)                tiến độ MO, đọc view `v_mo_progress`
    open_round(db, ...)                    mở một vòng mới
    rounds_of(db, mo_id)                   mọi vòng của một MO
    get_step(db, round_id, step_no)        None = trạm đó chưa nhận
    open_step(db, round_id, step_no, by)   mở một bước
    close_step(db, step, by)               đóng bước, ghi AI đóng
    steps_of(db, round_id)                 mọi bước của một vòng

`lock_open_round` là hàm mọi service sửa vòng đều phải gọi ĐẦU TIÊN: hai người
quét cùng lúc thì người sau đợi người trước xong hẳn mới đọc được trạng thái mới.
"""

from __future__ import annotations

import uuid
from collections import defaultdict

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.common import clock
from app.common.errors import NotFound
from app.modules.mo.models import ManufacturingOrder
from app.modules.round.models import MoRound, MoStep


def progress_row(db: Session, mo_id: uuid.UUID):
    """Tiến độ một MO — đọc thẳng view, KHÔNG cộng tay ở Python.

    Trả dòng thô (`quantity`, `qty_done`, `qty_remain`); `round_service.progress`
    bọc lại thành `Progress`. SQL thô vì đây là view, không có model để ORM bám vào.
    """
    return db.execute(
        text("SELECT quantity, qty_done, qty_remain FROM v_mo_progress WHERE mo_id = :m"),
        {"m": mo_id},
    ).one()


def lock_open_round(db: Session, mo_id: uuid.UUID) -> MoRound:
    """Khoá vòng đang mở. Mọi service sửa vòng đều bắt đầu bằng hàm này.

    Đây là chốt chống đua: hai người quét cùng lúc thì người sau đợi người trước
    xong hẳn mới đọc được trạng thái mới.
    """
    rnd = db.scalar(
        select(MoRound)
        .where(MoRound.mo_id == mo_id, MoRound.closed_at.is_(None))
        .with_for_update()
    )
    if rnd is None:
        raise NotFound("MO này không có vòng nào đang chạy")
    return rnd


def open_round(db: Session, *, mo: ManufacturingOrder, round_no: int, target_qty: int,
               required_sec: int, returned_to_step: int | None = None,
               reason: str | None = None) -> MoRound:
    """`returned_to_step` GHI thẳng vào vòng: 0 Kho (QC FAIL) · 3 Bàn team leader (thiếu SL)."""
    rnd = MoRound(
        mo_id=mo.id, round_no=round_no, target_qty=target_qty, required_sec=required_sec,
        returned_to_step=returned_to_step, return_reason_text=reason,
    )
    db.add(rnd)
    db.flush()
    return rnd


def rounds_of(db: Session, mo_id: uuid.UUID) -> list[MoRound]:
    """Mọi vòng của một MO, xếp theo số vòng — dùng cho bảng truy vết."""
    return list(db.scalars(
        select(MoRound).where(MoRound.mo_id == mo_id).order_by(MoRound.round_no)
    ))


def get_step(db: Session, round_id: uuid.UUID, step_no: int) -> MoStep | None:
    """Bước `step_no` của vòng. None = trạm đó chưa quét nhận."""
    return db.scalar(
        select(MoStep).where(MoStep.round_id == round_id, MoStep.step_no == step_no)
    )


def open_step(db: Session, round_id: uuid.UUID, step_no: int, by: uuid.UUID) -> MoStep:
    """Mở một bước — ghi mốc nhận và AI quét nhận."""
    step = MoStep(round_id=round_id, step_no=step_no, accepted_by=by)
    db.add(step)
    db.flush()
    return step


def close_step(db: Session, step: MoStep, by: uuid.UUID) -> None:
    """Bước N đóng khi bước N+1 quét nhận — KHÔNG có nút Complete riêng (BRD §9).

    `now()` lấy từ DB chứ không từ máy chủ ứng dụng: đồng hồ các máy lệch nhau
    thì thời gian từng bước không còn so được với nhau (BE-PLAN nguyên tắc ③).
    """
    if step.closed_at is None:
        step.closed_at = clock.db_now(db)
        step.closed_by = by


def steps_of(db: Session, round_id: uuid.UUID) -> list[MoStep]:
    """Mọi bước của một vòng, xếp theo thứ tự trạm."""
    return list(db.scalars(
        select(MoStep).where(MoStep.round_id == round_id).order_by(MoStep.step_no)
    ))


def steps_of_rounds(db: Session, round_ids: list[uuid.UUID]) -> dict[uuid.UUID, list[MoStep]]:
    """Bước của NHIỀU vòng trong một câu. Vòng chưa có bước nào thì thiếu khoá.

    Bản theo lô của `steps_of`. Màn hình truy vết hỏi cả chục vòng một lúc — hỏi
    từng vòng là số câu SQL tăng theo số vòng.
    """
    if not round_ids:
        return {}
    rows = db.scalars(
        select(MoStep).where(MoStep.round_id.in_(round_ids))
        .order_by(MoStep.round_id, MoStep.step_no)
    )
    theo_vong: dict[uuid.UUID, list[MoStep]] = defaultdict(list)
    for s in rows:
        theo_vong[s.round_id].append(s)
    return dict(theo_vong)
