"""Màn hình Báo cáo sản xuất — CHỈ ĐỌC. Không thao tác, không transaction.

    GET /reports/mo-progress           tiến độ từng lệnh
    GET /reports/hourly                sản lượng giờ theo khung, mỗi lệnh một chuỗi

**Hai đường này CỐ Ý không gác quyền theo trạm**, cùng lý do với `/board/running`
và `/board/counts`: BRD §9b.5 đặt màn tổng quan ra ngoài phạm vi xem theo trạm của
§12.4. Ở đây chỉ có số cộng dồn của cả xưởng, không có hàng đợi hay danh sách lệnh
đang nằm trong tay trạm nào — thứ mà §12.4 sinh ra để che.

Muốn siết lại thành `PLANNER` + `*_LEADER` thì sửa đúng hai chỗ: thêm
`require_any_role(...)` vào hai hàm dưới đây, và bỏ hai đường dẫn khỏi danh sách
`CO_Y_MO` trong `tests/test_permissions.py`. `actor.require_role()` hiện chỉ nhận
ĐÚNG MỘT vai nên phải viết thêm hàm nhận nhiều vai.

Cả hai đều đi qua `read_cache`: báo cáo trả cùng một dữ liệu cho mọi người, 50 máy
tính bảng cùng mở không có lý do gì chạy 50 lượt gộp.
"""

from __future__ import annotations

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Query

from app.common import read_cache
from app.common.deps import ActorDep, DbDep, PageDep
from app.common.schemas import Page
from app.common.vocab.enums import MoStatus
from app.modules.reports import service as reports_service
from app.modules.reports.schemas import HourlyOut, MoProgressRow

router = APIRouter(tags=["reports"])


@router.get("/reports/mo-progress", response_model=Page[MoProgressRow])
def report_mo_progress(
    db: DbDep,
    actor: ActorDep,
    page: PageDep,
    status: MoStatus | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
) -> dict:
    """MỘT TRANG tiến độ lệnh — đo bằng pcs ĐÃ ĐÓNG THÙNG nhập kho, không phải SL đạt."""
    limit, offset = page
    key = f"reports:progress:{status}:{date_from}:{date_to}:{limit}:{offset}"
    return read_cache.cached(
        key,
        lambda: reports_service.mo_progress(
            db, status=status, limit=limit, offset=offset,
            date_from=date_from, date_to=date_to,
        ),
    )


@router.get("/reports/hourly", response_model=HourlyOut)
def report_hourly(
    db: DbDep,
    actor: ActorDep,
    date_from: date,
    date_to: date,
    bucket: Annotated[int, Query(description="Khung gộp: 1 giờ · 4 giờ · cả ca")] = 1,
    codes: Annotated[list[str] | None, Query(description="Lọc theo mã lệnh")] = None,
) -> HourlyOut:
    """Sản lượng giờ đã gộp khung. Trả số thô — phần trăm tính ở nơi vẽ.

    Khoảng ngày và số mã lệnh đều có trần, xem `service._check_*`: khoá cache ghép
    từ chính tham số này nên miền giá trị phải hữu hạn.
    """
    key = f"reports:hourly:{bucket}:{date_from}:{date_to}:{sorted(codes) if codes else None}"
    return read_cache.cached(
        key,
        lambda: reports_service.hourly(
            db, bucket=bucket, date_from=date_from, date_to=date_to, codes=codes
        ),
    )
