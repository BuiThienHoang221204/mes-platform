"""Màn hình quét — dùng chung cho cả sáu trạm.

`warehouse_out`, `qc`, `step` đều được kích hoạt bằng cùng một payload này, nên chúng
ở chung một file dù là ba service khác nhau.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.common.schemas import StationNo


class ScanIn(BaseModel):
    raw: str = Field(
        examples=["XM068820"],
        description="Chuỗi thô từ đầu đọc — GIỮ NGUYÊN tiền tố, server tự bỏ phần trước chữ M",
    )


class ScanOut(BaseModel):
    ok: bool
    mo_code: str
    station: StationNo
    round_no: int
    message: str
    duplicate: bool = Field(
        default=False,
        description="Đầu đọc bắn hai lần trong 2 giây — trả lại kết quả lần trước, KHÔNG phải lỗi",
    )
