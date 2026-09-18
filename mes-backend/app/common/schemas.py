"""Kiểu dùng chung cho mọi màn hình."""

from __future__ import annotations

from typing import Annotated, Generic, TypeVar

from pydantic import BaseModel, Field, StringConstraints

T = TypeVar("T")

class Page(BaseModel, Generic[T]):
    """Một TRANG của một danh sách — khuôn DUY NHẤT cho mọi API trả danh sách.

    `total` là tổng số dòng SAU KHI lọc, không phải số dòng trong trang. Thiếu nó
    thì màn hình không biết còn trang sau hay không, và nút `Xem thêm` hoặc tắt vĩnh
    viễn hoặc bấm mãi không hết.

    Đừng đẻ khuôn thứ hai: hai khuôn thì FE phải nhớ endpoint nào trả kiểu nào, và
    chỗ nhớ nhầm không có gì bắt được.
    """

    items: list[T]
    total: int

MoCode = Annotated[str, Field(pattern=r"^M\d{6}$", examples=["M068820"])]
StationNo = Annotated[
    int,
    Field(ge=0, le=5, description="0 Kho · 1 Setup · 2 QC · 3 Bàn team leader · 4 SX · 5 Nhập kho"),
]

Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
"""Tên con hàng, tên người — bắt buộc có, không quá 200 ký tự."""

ReasonText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)]
"""Lý do BẮT BUỘC ghi: huỷ lệnh, QC không đạt, dừng chuyền."""

NoteText = Annotated[str, StringConstraints(strip_whitespace=True, max_length=500)]
"""Ghi chú tuỳ chọn — cho phép rỗng, chỉ chặn độ dài."""

EmployeeCode = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=32)]

Pin = Annotated[str, StringConstraints(min_length=1, max_length=64)]

MAX_IMPORT_ROWS = 2_000
"""Trần số DÒNG một lần nhập — một tệp Excel không được sinh quá ngần này lệnh."""

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
