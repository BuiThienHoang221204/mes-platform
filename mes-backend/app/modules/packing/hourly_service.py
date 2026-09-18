"""Đếm THÙNG theo giờ (§7b.2). Phòng Sản xuất, nằm trong trạm 4.

    add_packing_hourly(db, code, work_date, slot_hour, boxes…)

Để riêng khỏi `service.py` vì ghi ĐỘC LẬP với chốt sổ đóng thùng: đây là nhật ký
trong ca, `packing.qty_packed` mới là con số chốt của vòng. Hai sổ độc lập để đối
soát nhau — giống quan hệ giữa `hourly_output` và `production.qty_ok`.

**Thùng chỉ là cách ĐẾM; pcs mới là đơn vị gốc.** Tiến độ MO không bao giờ tính
bằng thùng: mọi ràng buộc sẵn có (`đạt + hỏng + thiếu = mục tiêu vòng`, cộng dồn ở
Nhập kho) đều chạy bằng pcs, mà đơn hàng hiếm khi chia hết cho quy cách.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date

from sqlalchemy.orm import Session

from app.common.errors import DomainError
from app.common.event_log import repository as event_repo
from app.common.uow import transactional
from app.common.vocab.action_codes import Act
from app.common.vocab.error_codes import Err
from app.modules.packing import repository as packing_repo
from app.modules.packing import service as packing_service
from app.modules.production import repository as production_repo
from app.modules.round import service as round_service


@dataclass(frozen=True)
class BoxTally:
    """Kết quả một lần ghi thùng, kèm hai số dẫn xuất của CẢ VÒNG."""

    boxes: int
    pcs_per_box: int
    packed_pcs: int
    made_pcs: int
    le_pcs: int


def _made_pcs(db: Session, round_id: uuid.UUID) -> int:
    """Số đã LÀM RA của vòng.

    Chốt sổ rồi thì lấy `qty_ok`; chưa thì tạm lấy Σ sản lượng giờ. Không lấy mục
    tiêu vòng: mục tiêu là số PHẢI làm, không phải số ĐÃ làm — lấy nhầm là cho phép
    đóng thùng hàng chưa tồn tại.
    """
    prod = production_repo.get_production(db, round_id)
    if prod is not None:
        return prod.qty_ok
    return sum(h.qty for h in production_repo.hourly_of(db, round_id))


@transactional
def add_packing_hourly(db: Session, *, code: str, work_date: date, slot_hour: int,
                       boxes: int, note: str | None, actor_id: uuid.UUID) -> BoxTally:
    """Ghi số thùng ĐẦY của một khung giờ.

    Quy cách lấy từ MO tại thời điểm ghi rồi **đóng dấu** vào dòng, nên sau này sửa
    quy cách cũng không làm sai các dòng cũ.

    Hai lớp chặn nằm ở CSDL, cố ý: UNIQUE `(vòng, ngày, khung giờ)` chặn ghi trùng,
    trigger `packing_hourly_within_made` chặn đóng nhiều hơn số đã làm ra. Để ở đó
    thì đúng cả khi có người ghi thẳng vào CSDL.
    """
    mo, rnd = round_service.lock_round(db, code)

    if mo.pcs_per_box <= 0:
        raise DomainError(
            f"{mo.code} chưa khai quy cách (pcs/thùng) — không đếm thùng được",
            code=Err.NO_PCS_PER_BOX,
        )
    # Ghi thùng đầu tiên tự mở sổ — không bắt bấm thêm một nút không hỏi gì.
    pack = packing_service.open_book(db, rnd, actor_id)
    if pack.completed_at is not None:
        raise DomainError("Đã kết thúc đóng thùng rồi — không ghi thêm", code=Err.PACK_DONE)

    packing_repo.add_packing_hourly(
        db, round_id=rnd.id, work_date=work_date, slot_hour=slot_hour,
        boxes=boxes, pcs_per_box=mo.pcs_per_box, note=note, by=actor_id,
    )

    packed = packing_repo.packed_boxes_pcs(db, rnd.id)
    made = _made_pcs(db, rnd.id)
    le = max(0, made - packed)

    event_repo.log(
        db, mo_id=rnd.mo_id, round_id=rnd.id, step_no=4, action=Act.PACK_HOURLY,
        reason=f"{work_date} {slot_hour:02d}h · {boxes} thùng × {mo.pcs_per_box} "
               f"= {boxes * mo.pcs_per_box} pcs" + (f" — còn lẻ {le}" if le else ""),
        actor_id=actor_id,
    )
    return BoxTally(boxes=boxes, pcs_per_box=mo.pcs_per_box,
                    packed_pcs=packed, made_pcs=made, le_pcs=le)
