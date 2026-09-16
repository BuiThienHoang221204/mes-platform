"""Luật của trạm 4 — chuyền và chốt sổ. Phòng Sản xuất.

    assign_line(db, rnd, line_code…)       mở quãng CHỜ  → TG chờ đếm
    line_start(db, rnd, line_code…)        đóng CHỜ, mở CHẠY → TG thực tế đếm
    line_hold(db, rnd, line_code…)         đóng CHẠY, mở CHỜ kèm lý do (§17)
    close_production(db, rnd, 3 số…)       chốt sổ + đóng mọi chuyền còn mở

Thời gian lưu bằng từng QUÃNG chứ không phải một cột cộng dồn — nhờ vậy mới biết
chuyền dừng lúc nào, vì sao. Ba số khi chốt do trigger ở DB canh, không kiểm ở đây.
"""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.common import clock
from app.common.errors import DomainError, Invalid
from app.common.event_log import repository as event_repo
from app.common.uow import transactional
from app.common.vocab.action_codes import Act
from app.common.vocab.enums import SegmentKind
from app.common.vocab.error_codes import Err
from app.common.vocab.state_names import State
from app.modules.catalog import repository as catalog_repo
from app.modules.production import repository as production_repo
from app.modules.production.models import LineSegment, Production
from app.modules.round import repository as round_repo
from app.modules.round import service as round_service


@transactional
def assign_line(db: Session, *, code: str, line_code: str, actor_id: uuid.UUID) -> LineSegment:
    """Thêm chuyền vào bảng → mở một đoạn CHỜ. TG chờ bắt đầu chạy từ đây (§11B)."""
    _, rnd = round_service.lock_round(db, code)
    if round_repo.get_step(db, rnd.id, 4) is None:
        raise DomainError("Sản xuất chưa quét nhận lệnh này", code=Err.NO_PRODUCTION_ACCEPT)
    line = catalog_repo.get_line(db, line_code)
    if production_repo.open_segment_of(db, rnd.id, line.id) is not None:
        raise DomainError(f"Chuyền {line_code} đã có trong vòng này rồi", code=Err.LINE_ADDED)

    seg = production_repo.save_segment(db, rnd.id, line.id,
                                       kind=SegmentKind.WAIT, by=actor_id)
    db.flush()
    event_repo.log(db, mo_id=rnd.mo_id, round_id=rnd.id, step_no=4, action=Act.RUN_ADD,
             to_state=State.WAITING, reason=f"Chuyền {line_code}", actor_id=actor_id)
    return seg

@transactional
def line_start(db: Session, *, code: str, line_code: str,
               actor_id: uuid.UUID) -> LineSegment:
    """Bấm Đang lắp ráp — đóng đoạn CHỜ, mở đoạn CHẠY."""
    _, rnd = round_service.lock_round(db, code)
    line = catalog_repo.get_line(db, line_code)
    cur = production_repo.open_segment_of(db, rnd.id, line.id)
    if cur is None:
        raise DomainError(f"Chuyền {line_code} chưa được thêm vào vòng này", code=Err.NO_LINE)
    if cur.kind == SegmentKind.RUN:
        raise DomainError(f"Chuyền {line_code} đang chạy rồi", code=Err.LINE_RUNNING)

    now = clock.db_clock(db)
    cur.ended_at = now
    cur.ended_by = actor_id
    seg = production_repo.save_segment(db, rnd.id, line.id, kind=SegmentKind.RUN,
                                       started_at=now, by=actor_id)
    db.flush()
    event_repo.log(db, mo_id=rnd.mo_id, round_id=rnd.id, step_no=4, action=Act.RUN_START,
             from_state=State.WAITING, to_state=State.ASSEMBLING,
             reason=f"Chuyền {line_code}", actor_id=actor_id)
    return seg

@transactional
def line_hold(db: Session, *, code: str, line_code: str, reason_code_id: int | None,
              reason_text: str | None, actor_id: uuid.UUID) -> LineSegment:
    """§17 — dừng máy BẮT BUỘC ghi lý do. Đóng đoạn CHẠY, mở đoạn CHỜ kèm lý do.

    Nhờ vậy TG thực tế đứng lại ngay và thời gian dừng rơi vào TG chờ — không ai
    ăn gian được giờ.
    """
    if not reason_code_id and not (reason_text or "").strip():
        raise Invalid("Dừng máy bắt buộc ghi lý do (§17)", code=Err.HOLD_REASON)
    _, rnd = round_service.lock_round(db, code)
    line = catalog_repo.get_line(db, line_code)
    cur = production_repo.open_segment_of(db, rnd.id, line.id)
    if cur is None or cur.kind != SegmentKind.RUN:
        raise DomainError(f"Chuyền {line_code} không đang chạy", code=Err.LINE_NOT_RUNNING)

    now = clock.db_clock(db)
    cur.ended_at = now
    cur.ended_by = actor_id
    seg = production_repo.save_segment(db, rnd.id, line.id, kind=SegmentKind.WAIT,
                                       started_at=now, by=actor_id,
                                       hold_reason_code_id=reason_code_id,
                                       hold_reason_text=reason_text)
    db.flush()
    event_repo.log(db, mo_id=rnd.mo_id, round_id=rnd.id, step_no=4, action=Act.RUN_HOLD,
             from_state=State.ASSEMBLING, to_state=State.WAITING,
             reason=f"Chuyền {line_code}: {reason_text or ''}", actor_id=actor_id)
    return seg

@transactional
def close_production(db: Session, *, code: str, qty_ok: int, qty_ng: int, qty_short: int,
                     ng_reason_code_id: int | None, ng_reason_text: str | None,
                     short_reason_code_id: int | None, short_reason_text: str | None,
                     actor_id: uuid.UUID) -> Production:
    """§16 — mọi chuyền đóng CÙNG MỘT MỐC. §7.5 — ba số cộng đúng bằng mục tiêu vòng.

    Ba số không kiểm ở đây: trigger `production_balances` lo, và nó đúng cả khi
    có người ghi thẳng vào DB.
    """
    _, rnd = round_service.lock_round(db, code)
    if round_repo.get_step(db, rnd.id, 4) is None:
        raise DomainError("Sản xuất chưa quét nhận lệnh này", code=Err.NO_PRODUCTION_ACCEPT)

    segs = production_repo.segments_of(db, rnd.id)
    if not segs:
        raise DomainError("Chưa gán chuyền nào cho vòng này", code=Err.NO_LINE)
    never_ran = {s.line_id for s in segs} - {s.line_id for s in segs if s.kind == SegmentKind.RUN}
    if never_ran:
        raise DomainError(
            "Còn chuyền chưa vào Đang lắp ráp — §16 yêu cầu đóng đồng bộ", code=Err.LINE_NOT_RUN
        )

    now = clock.db_clock(db)
    for seg in production_repo.open_segments_of(db, rnd.id):
        seg.ended_at = now
        seg.ended_by = actor_id

    row = production_repo.save_production(
        db, rnd.id, qty_ok=qty_ok, qty_ng=qty_ng, qty_short=qty_short,
        ng_reason_code_id=ng_reason_code_id, ng_reason_text=ng_reason_text,
        short_reason_code_id=short_reason_code_id, short_reason_text=short_reason_text,
        by=actor_id,
    )
    db.flush()

    step4 = round_repo.get_step(db, rnd.id, 4)
    if step4 is not None:
        round_repo.close_step(db, step4, actor_id)

    event_repo.log(db, mo_id=rnd.mo_id, round_id=rnd.id, step_no=4, action=Act.STEP4_FINISH_ALL,
             from_state=State.ASSEMBLING, to_state=State.FINISHED,
             reason=f"đạt {qty_ok} · hỏng {qty_ng} · thiếu {qty_short}", actor_id=actor_id)
    return row
