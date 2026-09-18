"""Hình dạng câu trả lời của màn Báo cáo sản xuất.

Trả SỐ THÔ, không trả phần trăm tính sẵn: FE còn gộp lại theo lệnh, theo khung giờ,
theo cả kỳ — có tỷ lệ tính sẵn thì không cộng lại được, và công thức `Đạt %` sinh ra
hai bản ở hai nơi.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.common.config import settings
from app.common.vocab.enums import MoStatus


class MoProgressRow(BaseModel):
    code: str
    product_name: str
    status: MoStatus
    quantity: int
    qty_done: int = Field(description="pcs ĐÃ ĐÓNG THÙNG nhập kho, không phải SL đạt (§6b.2)")
    qty_remain: int
    qty_ok_total: int
    qty_ng_total: int
    qty_short_total: int
    rounds_done: int


class HourlyPoint(BaseModel):
    at: datetime = Field(description="Đầu khung giờ")
    at_end: datetime = Field(description="Cuối khung — khung cuối ca ngắn hơn, nhãn phải nói thật")
    qty: int
    target_qty: int
    headcount: int | None
    slots: int = Field(description="Số dòng sổ đã gộp vào khung này")


class HourlySeries(BaseModel):
    code: str
    points: list[HourlyPoint]


class ShiftOut(BaseModel):
    """Sáu mốc giờ — trả kèm để FE vẽ nhãn theo, không chép tay hằng số sang JS."""

    day_start: int
    shift_start: int
    lunch_start: int
    lunch_end: int
    shift_end: int
    day_end: int

    @classmethod
    def current(cls) -> ShiftOut:
        r = settings.report
        return cls(
            day_start=r.day_start, shift_start=r.shift_start,
            lunch_start=r.lunch_start, lunch_end=r.lunch_end,
            shift_end=r.shift_end, day_end=r.day_end,
        )


class HourlyOut(BaseModel):
    bucket: int
    target_pct: int
    shift: ShiftOut
    series: list[HourlySeries]
    skipped_rows: int = Field(
        description="Dòng chưa khai định mức — loại khỏi CẢ tử lẫn mẫu, không coi là 0"
    )
    folded_rows: int = Field(
        description="Dòng ghi ngoài giờ đi làm, đã ghép vào khung gần nhất — tổng vẫn đúng"
    )
