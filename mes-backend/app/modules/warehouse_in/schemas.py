"""Màn hình Kho nhập — trạm 5, nơi MO đóng lại hoặc mở vòng mới."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

# Hai kết cục của một lần nhập kho. Khai Ở ĐÂY và `service.py` import lại, chứ không
# viết hai lần: viết hai lần thì thêm kết cục thứ ba mà quên một chỗ, trình kiểm kiểu
# không bắt được vì hai bên vẫn "đều là str".
Outcome = Literal["COMPLETED", "ROUND_OPENED"]


class WarehouseInCompleteIn(BaseModel):
    qty_received: int | None = Field(
        default=None, ge=0,
        description="Kho đếm lại, không bắt buộc — để trống thì lấy SL đã đóng thùng",
    )


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
