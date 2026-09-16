"""Vòng chạy và các bước — hình dạng dữ liệu của bảng truy vết.

CHƯA gắn làm `response_model` cho `/mos/{code}/trace`: endpoint đó còn trả `progress`,
`step_totals`, `events` — mà `response_model` thì lọc mất field lạ, không báo lỗi gì.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.common.schemas import StationNo


class StepOut(BaseModel):
    """Một bước của MỘT vòng.

    `closed_at` rỗng nghĩa là bước đang chạy — không có nút Hoàn thành, bước N
    đóng khi bước N+1 quét, và `closed_by` chính là người quét bước sau
    (BRD §1b.5).
    """

    step_no: StationNo
    name: str
    accepted_at: datetime
    accepted_by: str | None = None
    closed_at: datetime | None = None
    closed_by: str | None = None


class RoundOut(BaseModel):
    """Một vòng chạy cùng các bước của nó.

    `started_from` ĐỌC từ cột `returned_to_step` chứ KHÔNG suy ra từ việc vòng
    có bước Setup hay không: QC FAIL trả MO về Kho (0), thiếu SL trả về Bàn team leader
    (3), và suy ngược từ danh sách bước thì hai đường này nhìn giống hệt nhau.
    """

    round_no: int
    started_from: StationNo
    opened_at: datetime
    closed_at: datetime | None = None
    target_qty: int
    required_sec: int = Field(description="TG yêu cầu đã chia lại theo SL của riêng vòng này")
    return_reason_text: str | None = None
    steps: list[StepOut] = Field(default_factory=list)
