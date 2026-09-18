"""Màn hình điều hành — CHỈ ĐỌC. Không thao tác, không transaction.

    GET /board/running                 bảng lệnh đang chạy + KPI thời gian
    GET /board/queue/{station}         hàng chờ của một trạm
    GET /board/at/{station}            lệnh đang nằm trong tay một trạm
    GET /board/counts                  badge số lệnh từng trạm
    GET /mos/{code}/trace              cây truy vết đầy đủ của một MO
    GET /mos/{code}/rounds/{n}/hourly  một trang sản lượng giờ của một vòng
    GET /mos/{code}/rounds/{n}/boxes   một trang sổ thùng của một vòng

Mọi số liệu dẫn xuất đọc thẳng từ view, không tính lại ở Python (BE-PLAN nguyên
tắc ②) — để con số trên màn hình và con số trong báo cáo không bao giờ lệch nhau.
"""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter

from app.common import read_cache
from app.common.deps import ActorDep, DbDep, PageDep
from app.common.security.permissions import VIEW
from app.modules.board import service as board_service
from app.modules.board.schemas import StationCounts

router = APIRouter(tags=["board"])

@router.get("/board/running")
def board_running(db: DbDep, actor: ActorDep, page: PageDep) -> dict:
    """MỘT TRANG bảng lệnh ĐANG CHẠY — mỗi vòng đang mở một dòng, kèm KPI thời gian."""
    limit, offset = page
    return read_cache.cached(
        f"board:running:{limit}:{offset}",
        lambda: board_service.running_board(db, limit=limit, offset=offset))

@router.get("/board/queue/{station}")
def board_queue(station: int, db: DbDep, actor: ActorDep, page: PageDep) -> dict:
    """Hàng chờ một trạm: lệnh đã qua bước trước, chưa ai nhận ở trạm này.

    §12.4 — ngoài trạm của mình và trạm 4, không thấy gì: QC không mở được màn
    hình Kho, Kho không mở được màn hình QC. Trước đây luật này chỉ có ở giao diện,
    nên gõ thẳng URL hay gọi `curl` là đọc được hàng đợi của mọi phòng ban.
    """
    actor.require_step(station, VIEW)
    limit, offset = page
    return read_cache.cached(
        f"board:queue:{station}:{limit}:{offset}",
        lambda: board_service.queue(db, station, limit=limit, offset=offset))

@router.get("/board/at/{station}")
def board_at_station(station: int, db: DbDep, actor: ActorDep, page: PageDep) -> dict:
    """MỘT TRANG lệnh ĐANG ở trạm này: đã quét nhận, chưa trạm sau lấy đi."""
    actor.require_step(station, VIEW)
    limit, offset = page
    return read_cache.cached(
        f"board:at:{station}:{limit}:{offset}",
        lambda: board_service.at_station(db, station, limit=limit, offset=offset))

@router.get("/board/counts", response_model=StationCounts)
def board_counts(db: DbDep, actor: ActorDep,
                 date_from: date | None = None,
                 date_to: date | None = None) -> StationCounts:
    """Số lệnh chờ ở từng trạm — con số trên badge thanh trạm.

    Riêng Kho đếm cả lệnh chờ nhận lẫn lệnh đã nhận chưa bàn giao.

    `date_from`/`date_to` thu hẹp TẬP LỆNH được đếm theo ngày tạo. Đây vẫn là ảnh chụp
    HIỆN TẠI — nó không dựng lại được tình trạng xưởng của một ngày đã qua, muốn thế
    phải phát lại nhật ký. Không truyền gì thì đếm toàn bộ, đúng như badge sidebar cần.
    """
    waiting, holding = read_cache.cached(
        f"board:counts:{date_from}:{date_to}",
        lambda: board_service.station_counts(db, date_from=date_from, date_to=date_to),
    )
    return StationCounts(counts=waiting, holding=holding)

@router.get("/mos/{code}/events")
def mo_events(code: str, db: DbDep, actor: ActorDep, limit: int = 10, offset: int = 0) -> dict:
    """Một TRANG nhật ký của MO — nút Xem thêm gọi endpoint này.

    Tách khỏi `trace` vì nhật ký là phần duy nhất của truy cứu lớn không giới hạn:
    một MO chạy nhiều vòng có hàng trăm dòng, mà màn hình chỉ hiện mười.
    """
    actor.require_step(4, VIEW)
    return board_service.events(
        db, code, limit=max(1, min(limit, 100)), offset=max(0, offset)
    )

@router.get("/mos/{code}/rounds/{round_no}/hourly")
def round_hourly(code: str, round_no: int, db: DbDep, actor: ActorDep, page: PageDep) -> dict:
    """MỘT TRANG sản lượng giờ của một vòng — nút Xem thêm của màn truy cứu.

    Tách khỏi `trace` vì đây là một trong hai danh sách KHÔNG có trần trong cây truy
    cứu: `steps` tối đa 6, `lines` tối đa 14, số vòng hiếm khi quá 5 — còn sổ giờ thì
    một vòng chạy một tuần đã ~56 dòng, chạy một tháng là hơn hai trăm.
    """
    actor.require_step(4, VIEW)
    limit, offset = page
    return board_service.round_hourly(db, code, round_no, limit=limit, offset=offset)

@router.get("/mos/{code}/rounds/{round_no}/boxes")
def round_boxes(code: str, round_no: int, db: DbDep, actor: ActorDep, page: PageDep) -> dict:
    """MỘT TRANG sổ thùng theo giờ của một vòng."""
    actor.require_step(4, VIEW)
    limit, offset = page
    return board_service.round_boxes(db, code, round_no, limit=limit, offset=offset)

@router.get("/mos/{code}/trace")
def trace(code: str, db: DbDep, actor: ActorDep) -> dict:
    """Truy vết một MO: mọi vòng, từng bước, năng suất chuyền, sản lượng giờ, nhật ký."""
    actor.require_step(4, VIEW)
    return board_service.trace(db, code)
