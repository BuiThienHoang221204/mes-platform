"""Vòng chạy — mở và đóng. DUY NHẤT một chỗ trong cả hệ thống.

    Progress                               qty_done · qty_remain · quantity
    lock_round(db, code)                   tra MO theo mã + KHOÁ vòng đang mở
    progress(db, mo_id)                    đọc tiến độ từ view
    required_sec_for(mo, target_qty)       chia lại TG yêu cầu theo SL của vòng
    open_first_round(db, mo, actor_id)     vòng 1 — gọi từ Submit
    open_next_round(db, …returned_to_step) vòng tiếp — QC FAIL (0) hoặc thiếu SL (3)
    close_round_completed(db, mo, …)       đủ SL → đóng vòng và đóng MO

`open_next_round` GHI `returned_to_step` chứ không để suy ra sau — QC FAIL (0) và
thiếu SL (3) nhìn giống hệt nhau nếu suy ngược từ danh sách bước.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.common import clock
from app.common.errors import DomainError
from app.common.event_log import repository as event_repo
from app.common.vocab.action_codes import Act
from app.common.vocab.enums import RETURN_TO_BANCHO, RETURN_TO_KHO, MoStatus
from app.common.vocab.state_names import round_label
from app.modules.mo import repository as mo_repo
from app.modules.mo.models import ManufacturingOrder
from app.modules.production import repository as production_repo
from app.modules.round import repository as round_repo
from app.modules.round.models import MoRound


@dataclass(frozen=True)
class Progress:
    """Tiến độ một MO. `qty_done` tính theo SL ĐÃ ĐÓNG THÙNG, không theo SL đạt (§6b.2)."""
    quantity: int
    qty_done: int       # SL ĐÃ ĐÓNG THÙNG cộng dồn — BRD §6b.2
    qty_remain: int


def lock_round(db: Session, code: str) -> tuple[ManufacturingOrder, MoRound]:
    """Tra MO theo mã rồi KHOÁ vòng đang mở của nó. Mở đầu mọi thao tác sửa vòng.

    Phải gọi TRONG `transaction()`: khoá dòng chỉ sống bên trong một giao dịch và
    nhả ngay lúc commit. Gọi ngoài giao dịch thì câu lệnh vẫn chạy nhưng khoá tan
    liền — hai người bấm cùng lúc sẽ cùng đi qua.
    """
    mo = mo_repo.get_mo(db, code)
    return mo, round_repo.lock_open_round(db, mo.id)


def progress(db: Session, mo_id: uuid.UUID) -> Progress:
    """Tiến độ một MO. Câu truy vấn ở `round_repo.progress_row`."""
    row = round_repo.progress_row(db, mo_id)
    return Progress(quantity=row.quantity, qty_done=row.qty_done, qty_remain=row.qty_remain)


def required_sec_for(mo: ManufacturingOrder, target_qty: int) -> int:
    """Hạn mức của vòng = thời gian yêu cầu của cả MO CHIA THEO SL của vòng (BRD §7.3).

    Vòng 2 chỉ làm 1.000/10.000 thì chỉ được 1/10 thời gian — nếu không thì vòng
    nào cũng Đạt.
    """
    return max(1, round(mo.required_production_sec * target_qty / mo.quantity))


def open_first_round(db: Session, mo: ManufacturingOrder, actor_id: uuid.UUID) -> MoRound:
    """Gọi lúc Submit. Vòng 1 luôn bắt đầu ở Kho."""
    rnd = round_repo.open_round(
        db, mo=mo, round_no=1, target_qty=mo.quantity,
        required_sec=mo.required_production_sec, returned_to_step=RETURN_TO_KHO,
    )
    event_repo.log(db, mo_id=mo.id, round_id=rnd.id, action=Act.ROUND_OPEN,
             to_state=round_label(rnd.round_no), actor_id=actor_id)
    return rnd


def open_next_round(db: Session, *, mo: ManufacturingOrder, current: MoRound,
                    returned_to_step: int, reason: str, actor_id: uuid.UUID) -> MoRound:
    """Đóng vòng hiện tại rồi mở vòng mới.

    `returned_to_step` chỉ có hai giá trị và chúng khác hẳn nhau (BRD §6b.1):
      3 Bàn team leader — thiếu SL hoặc dừng quá lâu. Máy setup đúng, hàng đã qua QC.
      0 Kho     — QC FAIL. Setup sai thì phải làm lại từ gốc.
    """
    if returned_to_step not in (RETURN_TO_KHO, RETURN_TO_BANCHO):
        raise DomainError("Vòng mới chỉ quay về Kho (0) hoặc Bàn team leader (3)")

    _close_open_segments(db, current.id, actor_id)
    current.closed_at = clock.db_now(db)
    current.returned_to_step = returned_to_step
    current.return_reason_text = reason
    db.flush()

    p = progress(db, mo.id)
    if p.qty_remain <= 0:
        raise DomainError("Đơn đã đủ SL — không mở vòng mới")

    nxt = round_repo.open_round(
        db, mo=mo, round_no=current.round_no + 1, target_qty=p.qty_remain,
        required_sec=required_sec_for(mo, p.qty_remain), returned_to_step=returned_to_step,
    )

    # Về Bàn team leader thì MỞ SẴN bước 3 — MO nằm luôn ở hàng đợi Sản xuất, không phải
    # in lại phiếu, không setup lại, không QC lại (BRD §6b.2).
    if returned_to_step == RETURN_TO_BANCHO:
        round_repo.open_step(db, nxt.id, RETURN_TO_BANCHO, actor_id)

    event_repo.log(db, mo_id=mo.id, round_id=current.id,
             action=Act.RETURN_KHO if returned_to_step == RETURN_TO_KHO else Act.RETURN_BANCHO,
             from_state=round_label(current.round_no), to_state=round_label(nxt.round_no),
             reason=f"{reason} — đã xong {p.qty_done}/{p.quantity}, còn {p.qty_remain}",
             actor_id=actor_id)
    return nxt


def close_round_completed(db: Session, *, mo: ManufacturingOrder, current: MoRound,
                          actor_id: uuid.UUID) -> None:
    """Đủ SL — đóng vòng cuối và đóng luôn đơn hàng."""
    _close_open_segments(db, current.id, actor_id)
    current.closed_at = clock.db_now(db)
    mo.status = MoStatus.COMPLETED
    db.flush()
    event_repo.log(db, mo_id=mo.id, round_id=current.id, action=Act.MO_COMPLETE,
             from_state=MoStatus.PROCESSING, to_state=MoStatus.COMPLETED, actor_id=actor_id)


def _close_open_segments(db: Session, round_id: uuid.UUID, actor_id: uuid.UUID) -> None:
    """Đóng vòng thì không để đoạn chuyền nào treo — nếu không đồng hồ chạy mãi."""
    now = clock.db_clock(db)
    for seg in production_repo.open_segments_of(db, round_id):
        seg.ended_at = now
        seg.ended_by = actor_id
