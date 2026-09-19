"""Bảng điều hành: hàng chờ từng trạm · badge trên thanh trạm · bảng đang chạy."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from app.common.schemas import StationNo


class QueueRow(BaseModel):
    code: str
    product_name: str
    quantity: int
    round_no: int
    target_qty: int


class StationCounts(BaseModel):
    """Hai con số cho mỗi trạm, không phải một.

    `counts` là việc CHƯA AI NHẬN — có người phải đi quét. `holding` là việc ĐANG
    trong tay trạm — đang chạy, không ai cần làm gì thêm.

    Gộp lại một số thì xưởng chạy ba lệnh ở Sản xuất mà màn hình hiện 0 khắp nơi,
    và người đọc tưởng hệ thống hỏng.
    """

    counts: dict[StationNo, int]
    holding: dict[StationNo, int]


class OverviewAlert(BaseModel):
    """MỘT việc cần chú ý, ở dạng DỮ LIỆU — không phải câu chữ.

    Máy chủ trả `kind` kèm số liệu, màn hình tự dựng câu tiếng Việt. Dựng câu ở đây
    thì mỗi lần sửa lời phải triển khai lại backend và viết lại test, trong khi câu
    chữ là thứ hay sửa nhất. Đổi lại còn gọn hơn: một cảnh báo dạng dữ liệu tốn
    khoảng 70 byte, cùng nội dung viết thành câu tốn hơn 150.
    """

    kind: Literal["HOLD", "LATE", "REWORK", "RE_ROUND"]
    code: str
    round_no: int
    lines: list[str] = []
    reason: str | None = None
    late_sec: int | None = None
    required_sec: int | None = None
    target_qty: int | None = None
    quantity: int | None = None


class BoardOverview(BaseModel):
    """Tất cả những gì màn Tổng quan cần, trong MỘT lời gọi.

    Trước đây màn này gọi ba endpoint rồi tự tính: `board/running?limit=100` (43 kB),
    `board/queue/0?limit=100` (2 kB) và danh sách MO đã hoàn thành — cứ 10 giây một
    lượt, chỉ để rút ra năm con số và một danh sách cảnh báo. Endpoint này trả thẳng
    kết quả, khoảng 4 kB.
    """

    running_rounds: int
    lines_total: int
    lines_busy: int
    lines_held: int
    rework: int
    re_round: int
    completed: int
    alerts: list[OverviewAlert]
    alerts_total: int
