"""Ghi sản lượng theo giờ. Vai LEADER.

    add_hourly(db, rnd, work_date, slot_hour, headcount, target_qty, qty…)

Để riêng khỏi `service.py` vì ghi ĐỘC LẬP với chốt sổ: hai người khác nhau làm.
Chỉ ghi được khi đang có chuyền chạy; trùng khung giờ thì chỉ mục ở DB chặn.
"""

from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy.orm import Session

from app.common.errors import DomainError, Invalid
from app.common.event_log import repository as event_repo
from app.common.uow import transactional
from app.common.vocab.action_codes import Act
from app.common.vocab.enums import SegmentKind
from app.common.vocab.error_codes import Err
from app.modules.production import repository as production_repo
from app.modules.round import service as round_service


@transactional
def add_hourly(db: Session, *, code: str, work_date: date, slot_hour: int,
               headcount: int, target_qty: int, qty: int,
               note: str | None, actor_id: uuid.UUID):
    """Ghi THEO MO chứ không theo chuyền (§7.2b). BA số, cả ba bắt buộc.

    Trigger `hourly_within_target` chặn Σ thực tế vượt mục tiêu vòng, UNIQUE chặn
    trùng khung giờ của cùng một ngày. Hai số kia không có ràng buộc chéo nào —
    vượt `target_qty` của một khung là **tin tốt**, không phải lỗi.
    """
    _, rnd = round_service.lock_round(db, code)
    if not any(s.kind == SegmentKind.RUN and s.ended_at is None
               for s in production_repo.segments_of(db, rnd.id)):
        raise DomainError("Chỉ khi Đang lắp ráp mới ghi được sản lượng giờ", code=Err.NOT_RUNNING)
    if headcount <= 0:
        raise Invalid("Số người phải lớn hơn 0", code=Err.HOURLY_PEOPLE)
    if target_qty <= 0:
        raise Invalid("Sản lượng yêu cầu phải lớn hơn 0", code=Err.HOURLY_TARGET)

    row = production_repo.add_hourly(
        db, round_id=rnd.id, work_date=work_date, slot_hour=slot_hour,
        headcount=headcount, target_qty=target_qty, qty=qty, note=note, by=actor_id)
    event_repo.log(db, mo_id=rnd.mo_id, round_id=rnd.id, step_no=4, action=Act.HOURLY_ADD,
             reason=f"{work_date} {slot_hour:02d}h · thực tế {qty}/{target_qty} · "
                    f"{headcount} người", actor_id=actor_id)
    return row
