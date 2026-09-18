"""Truy vấn bảng `manufacturing_order`.

    get_mo(db, code)                       NÉM lỗi nếu không có
    list_mos(db, status, limit, offset)    MỘT TRANG danh sách lệnh, mới nhất trước
    count_mos(db, status)                  tổng số lệnh sau khi lọc
    get_mo_or_none(db, code)               trả None nếu không có

`get_mo` dùng ở đường đi chính nơi thiếu MO là sai; `get_mo_or_none` dùng khi
đang KIỂM xem mã đã tồn tại chưa.
"""

from __future__ import annotations

import uuid
from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.common.config import settings
from app.common.errors import NotFound
from app.common.vocab.enums import MoStatus
from app.modules.mo.models import ManufacturingOrder


def save_mo(db: Session, *, code: str, product_name: str, quantity: int,
            required_production_sec: int, pcs_per_box: int, by: uuid.UUID) -> ManufacturingOrder:
    """Ghi một lệnh mới, trạng thái DRAFT. `UNIQUE (code)` chặn trùng mã lúc flush."""
    mo = ManufacturingOrder(
        code=code, product_name=product_name, quantity=quantity,
        required_production_sec=required_production_sec, pcs_per_box=pcs_per_box,
        created_by=by,
    )
    db.add(mo)
    return mo


def get_mo(db: Session, code: str) -> ManufacturingOrder:
    """Không có thì NÉM lỗi — dùng ở đường đi chính, nơi thiếu MO là sai."""
    mo = db.scalar(select(ManufacturingOrder).where(ManufacturingOrder.code == code))
    if mo is None:
        raise NotFound(f"Không có MO {code} trong hệ thống")
    return mo


def get_mo_or_none(db: Session, code: str) -> ManufacturingOrder | None:
    """Không có thì trả None — dùng khi đang KIỂM xem mã đã tồn tại chưa."""
    return db.scalar(select(ManufacturingOrder).where(ManufacturingOrder.code == code))


def _local(col):
    """Mốc `timestamptz` quy về giờ tường của xưởng."""
    return func.timezone(settings.tz, col)


def _mos_where(status: MoStatus | None,
               date_from: date | None = None, date_to: date | None = None):
    """Vế lọc dùng CHUNG cho cả câu lấy dòng lẫn câu đếm tổng.

    `created_at` là `timestamptz`, còn người dùng chọn NGÀY trên tờ lịch của xưởng.
    Quy đổi bằng `timezone(settings.tz, …)` chứ không so thẳng: so thẳng thì ý nghĩa
    của "ngày" phụ thuộc biến `TimeZone` của máy chủ CSDL. Máy phát triển đang để
    `Asia/Ho_Chi_Minh` nên nhìn thì đúng, nhưng container chạy test để UTC — cùng một
    dữ liệu mà lệch nhau một ngày, và không có gì báo.

    `to` cộng thêm một ngày vì mốc có giờ phút: so `<= to` là mất sạch lệnh tạo trong
    ngày cuối, chỉ giữ đúng lệnh tạo lúc 00:00:00.

    Đổi lại, bọc cột trong hàm thì chỉ mục trên `created_at` hết dùng được — chấp nhận
    được vì bảng này chưa có chỉ mục nào trên cột đó, và đúng ngày là thứ không đánh đổi.
    """
    stmt = select(ManufacturingOrder)
    if status is not None:
        stmt = stmt.where(ManufacturingOrder.status == status)
    if date_from is not None:
        stmt = stmt.where(_local(ManufacturingOrder.created_at) >= date_from)
    if date_to is not None:
        stmt = stmt.where(_local(ManufacturingOrder.created_at) < date_to + timedelta(days=1))
    return stmt


def list_mos(db: Session, *, status: MoStatus | None = None,
             date_from: date | None = None, date_to: date | None = None,
             limit: int, offset: int = 0) -> list[ManufacturingOrder]:
    """MỘT TRANG danh sách lệnh, mới tạo trước.

    Màn Kế hoạch cần cái này: lệnh vừa tạo ở trạng thái DRAFT không nằm trong
    hàng đợi trạm nào cả, nên không có đường nào khác để tìm lại nó.

    `limit` KHÔNG có mặc định — có lúc nó là `200` viết cứng ở đây, router không
    truyền gì và cũng không trả tổng số. Tới lệnh thứ 201 là màn hình **mất lệnh mà
    không báo gì** — người dùng tưởng chưa tạo được rồi tạo lại. Bắt người gọi khai
    rõ thì không ai cắt dữ liệu sau lưng ai nữa.

    Sắp theo `(created_at DESC, code)`: thiếu khoá phụ thì hai lệnh tạo cùng một
    khoảnh khắc có thể đổi chỗ giữa hai lần gọi — trang 1 và trang 2 cùng chứa một
    dòng, và một dòng khác biến mất khỏi cả hai.
    """
    return list(db.scalars(
        _mos_where(status, date_from, date_to)
        .order_by(ManufacturingOrder.created_at.desc(), ManufacturingOrder.code)
        .limit(limit).offset(offset)
    ))


def count_mos(db: Session, *, status: MoStatus | None = None,
              date_from: date | None = None, date_to: date | None = None) -> int:
    """Tổng số lệnh SAU KHI lọc — đếm từ đúng vế lọc của `list_mos`."""
    return db.scalar(
        select(func.count()).select_from(_mos_where(status, date_from, date_to).subquery())
    ) or 0
