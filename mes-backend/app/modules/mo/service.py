"""Luật của lệnh sản xuất trước khi xuống xưởng. Vai PLANNER.

    NewMo                                  dữ liệu một lệnh sắp tạo
    create(db, items, actor_id)            tạo lệnh — MỘT transaction cho cả danh sách
    parse_csv(csv)                         đọc CSV 4 cột
    submit(db, mo, actor_id)               chốt lệnh + MỞ VÒNG 1
    cancel(db, mo, reason, actor_id)       huỷ kèm lý do

`submit` là ranh giới của module: trước đó lệnh còn sửa, sau đó khoá cứng. Nó cũng
là chỗ DUY NHẤT gọi `round_service.open_first_round` — MO có vòng từ đây.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.common import clock
from app.common.errors import DomainError, Invalid
from app.common.event_log import repository as event_repo
from app.common.uow import transactional
from app.common.vocab.action_codes import Act
from app.common.vocab.enums import MoStatus
from app.common.vocab.error_codes import Err
from app.modules.mo import repository as mo_repo
from app.modules.mo.models import ManufacturingOrder
from app.modules.round import repository as round_repo
from app.modules.round import service as round_service
from app.modules.scan.mocode import MO_STRICT, normalize


@dataclass(frozen=True)
class NewMo:
    """Dữ liệu một lệnh sắp tạo. `required_production_sec` là GIÂY, FE gửi lên phút."""
    code: str
    product_name: str
    quantity: int
    required_production_sec: int
    pcs_per_box: int = 0


def _check_code(code: str) -> str:
    c = normalize(code)
    if not MO_STRICT.match(c):
        raise Invalid(
            f'Mã "{code}" sai định dạng — cần chữ M kèm đúng 6 chữ số', code=Err.MO_CODE
        )
    return c


@transactional
def create(db: Session, items: list[NewMo], actor_id: uuid.UUID) -> list[ManufacturingOrder]:
    """Tạo lệnh. Nhận DANH SÁCH vì `POST /mos/import` đưa cả file CSV vào một lần;
    `POST /mos` chỉ truyền một phần tử.
    """
    if not items:
        raise Invalid("Danh sách rỗng")
    made: list[ManufacturingOrder] = []
    for it in items:
        if it.quantity <= 0:
            raise Invalid(f"{it.code}: số lượng phải lớn hơn 0")
        if it.required_production_sec <= 0:
            raise Invalid(f"{it.code}: thời gian yêu cầu phải lớn hơn 0")
        made.append(mo_repo.save_mo(
            db, code=_check_code(it.code), product_name=it.product_name,
            quantity=it.quantity, required_production_sec=it.required_production_sec,
            pcs_per_box=it.pcs_per_box, by=actor_id,
        ))
    db.flush()
    for mo in made:
        event_repo.log(db, mo_id=mo.id, action=Act.MO_CREATE, to_state=MoStatus.DRAFT,
                 reason=f"{mo.product_name} · {mo.quantity} {mo.unit}", actor_id=actor_id)
    return made


def parse_csv(text_body: str) -> list[NewMo]:
    """4 cột bắt buộc + 1 tuỳ chọn:

        Mã, Tên con hàng, Số lượng, TG yêu cầu Step4 (phút)[, Quy cách pcs/thùng]

    Cột 5 thêm SAU nên phải để tuỳ chọn — file CSV cũ của xưởng vẫn nhập được,
    và thiếu nó thì quy cách là 0 = mặt hàng không đóng thùng.
    """
    items: list[NewMo] = []
    for line in (line.strip() for line in text_body.splitlines()):
        if not line:
            continue
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 4:
            raise Invalid(f'Dòng invalid định dạng: "{line}" — cần 4 cột')
        try:
            qty, mins = int(parts[2]), int(parts[3])
            box = int(parts[4]) if len(parts) > 4 and parts[4] else 0
        except ValueError as exc:
            raise Invalid(f'Dòng invalid số: "{line}"') from exc
        items.append(NewMo(parts[0], parts[1], qty, mins * 60, box))
    return items


@transactional
def submit(db: Session, code: str, actor_id: uuid.UUID) -> None:
    """Submit khoá cứng đơn VÀ mở vòng 1 — từ đây MO có mặt ở hàng đợi Kho."""
    mo = mo_repo.get_mo(db, code)
    if mo.status != MoStatus.DRAFT:
        raise DomainError(f"{mo.code} đã Submit rồi", code=Err.ALREADY_SUBMITTED)
    mo.status = MoStatus.PROCESSING
    mo.submitted_at = clock.db_now(db)
    db.flush()
    round_service.open_first_round(db, mo, actor_id)
    event_repo.log(db, mo_id=mo.id, action=Act.MO_SUBMIT,
             from_state=MoStatus.DRAFT, to_state=MoStatus.PROCESSING, actor_id=actor_id)


@transactional
def cancel(db: Session, code: str, reason: str, actor_id: uuid.UUID) -> None:
    """Huỷ lệnh kèm lý do bắt buộc. Bản ghi giữ nguyên, không xoá (§2.3, §4A)."""
    mo = mo_repo.get_mo(db, code)
    if not (reason or "").strip():
        raise Invalid("Huỷ lệnh bắt buộc ghi lý do (§2.3)")
    if mo.status == MoStatus.COMPLETED:
        raise DomainError("Đơn đã hoàn thành — không huỷ được")
    before = mo.status
    mo.status = MoStatus.CANCELLED
    mo.cancel_reason_text = reason
    mo.cancelled_at = clock.db_now(db)
    mo.cancelled_by = actor_id
    for rnd in round_repo.rounds_of(db, mo.id):
        if rnd.closed_at is None:
            rnd.closed_at = mo.cancelled_at
            rnd.return_reason_text = f"Huỷ lệnh: {reason}"
    db.flush()
    event_repo.log(db, mo_id=mo.id, action=Act.MO_CANCEL, from_state=before,
                   to_state=MoStatus.CANCELLED, reason=reason, actor_id=actor_id)
