"""Bảng điều hành: hàng chờ từng trạm · badge trên thanh trạm · bảng đang chạy."""

from __future__ import annotations

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
