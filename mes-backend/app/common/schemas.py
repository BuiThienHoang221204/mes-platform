"""Kiểu dùng chung cho mọi màn hình."""

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, Field

MoCode = Annotated[str, Field(pattern=r"^M\d{6}$", examples=["M068820"])]
StationNo = Annotated[
    int,
    Field(ge=0, le=5, description="0 Kho · 1 Setup · 2 QC · 3 Bàn team leader · 4 SX · 5 Nhập kho"),
]


class ErrorOut(BaseModel):
    """Hình dạng lỗi thống nhất cho mọi endpoint.

    `message` luôn là câu tiếng Việt cho người vận hành đọc thẳng trên màn hình
    xưởng — xem app/core/errors.py.
    """

    code: str
    message: str


class OkOut(BaseModel):
    ok: bool = True
    message: str = ""
