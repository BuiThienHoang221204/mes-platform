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
    """Badge mỗi trạm.

    Riêng Kho (0) đếm HAI nhóm rời nhau: lệnh chờ nhận và lệnh đã nhận nhưng
    chưa bàn giao. Bỏ nhóm thứ hai thì badge hiện 0 trong khi MO còn nằm ở Kho.
    """

    counts: dict[StationNo, int]
