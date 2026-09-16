"""Màn hình điều hành — CHỈ ĐỌC. Không thao tác, không transaction.

    GET /board/running                 bảng lệnh đang chạy + KPI thời gian
    GET /board/queue/{station}         hàng chờ của một trạm
    GET /board/at/{station}            lệnh đang nằm trong tay một trạm
    GET /board/counts                  badge số lệnh từng trạm
    GET /mos/{code}/trace              cây truy vết đầy đủ của một MO

Mọi số liệu dẫn xuất đọc thẳng từ view, không tính lại ở Python (BE-PLAN nguyên
tắc ②) — để con số trên màn hình và con số trong báo cáo không bao giờ lệch nhau.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.common.deps import ActorDep, DbDep
from app.common.security.permissions import VIEW
from app.modules.board import service as board_service
from app.modules.board.schemas import StationCounts

router = APIRouter(tags=["board"])


@router.get("/board/running")
def board_running(db: DbDep, actor: ActorDep) -> list[dict]:
    """Bảng lệnh ĐANG CHẠY — mỗi vòng đang mở một dòng, kèm KPI thời gian."""
    return board_service.running_board(db)


@router.get("/board/queue/{station}")
def board_queue(station: int, db: DbDep, actor: ActorDep) -> list[dict]:
    """Hàng chờ một trạm: lệnh đã qua bước trước, chưa ai nhận ở trạm này."""
    # CHƯA gắn response_model=list[QueueRow]: hàng đợi trạm 5 trả thêm
    # qty_packed, mà response_model thì lọc mất field lạ — không báo lỗi gì.
    return board_service.queue(db, station)


@router.get("/board/at/{station}")
def board_at_station(station: int, db: DbDep, actor: ActorDep) -> list[dict]:
    """Lệnh ĐANG ở trạm này: đã quét nhận, chưa trạm sau lấy đi."""
    return board_service.at_station(db, station)


@router.get("/board/counts", response_model=StationCounts)
def board_counts(db: DbDep, actor: ActorDep) -> StationCounts:
    """Số lệnh chờ ở từng trạm — con số trên badge thanh trạm.
    Riêng Kho đếm cả lệnh chờ nhận lẫn lệnh đã nhận chưa bàn giao."""
    return StationCounts(counts=board_service.station_counts(db))


@router.get("/mos/{code}/trace")
def trace(code: str, db: DbDep, actor: ActorDep) -> dict:
    """Truy vết một MO: mọi vòng, từng bước, năng suất chuyền, sản lượng giờ, nhật ký."""
    # Trả TOÀN BỘ lịch sử một MO. Trước đây bất kỳ ai đăng nhập đều xem được.
    actor.require_step(4, VIEW)
    # CHƯA gắn response_model: còn trả progress, step_totals, events ngoài
    # rounds — xem app/modules/round/schemas.py.
    return board_service.trace(db, code)
