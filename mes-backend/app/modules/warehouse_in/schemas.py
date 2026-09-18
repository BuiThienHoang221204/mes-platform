"""Màn hình Kho nhập — trạm 5, nơi MO đóng lại hoặc mở vòng mới."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

Outcome = Literal["COMPLETED", "ROUND_OPENED"]

class WarehouseInCompleteOut(BaseModel):
    """Hai kết cục khác hẳn nhau — FE phải phân nhánh theo `outcome`.

    COMPLETED: đủ SL, MO đóng. ROUND_OPENED: còn thiếu, server mở vòng mới
    ngay trong cùng transaction và MO quay về Bàn team leader (3).
    """

    outcome: Outcome
    qty_done: int
    qty_remain: int
    new_round_no: int | None = None
    message: str
