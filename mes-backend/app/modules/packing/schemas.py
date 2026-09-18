"""Màn hình Đóng thùng — chạy SONG SONG với Sản xuất, không phải một bước nối tiếp."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field

from app.common.schemas import NoteText


class PackingFinishIn(BaseModel):
    """`qty_packed` là con số đẩy tiến độ MO (BRD §6b.2), không phải `qty_ok`.

    Hàng đạt mà chưa đóng thùng thì chưa tính — view `v_mo_progress` cộng theo
    cột này. §10 #38 chưa chốt: nếu xưởng luôn đóng thùng đúng bằng SL đạt thì ô
    nhập này bỏ được, server tự điền.
    """

    qty_packed: int = Field(gt=0)
    note_text: NoteText | None = None


class PackingHourlyIn(BaseModel):
    """Số THÙNG ĐẦY đóng được trong một khung giờ.

    Chỉ đếm thùng ĐẦY. Thùng lẻ chỉ đóng khi biết chắc không còn hàng nào tới nữa —
    tức là lúc `POST /packing/{code}/finish`, và nó vào `qty_packed`. Cho ghi thùng
    lẻ từng giờ thì phép `boxes × pcs_per_box` hết đúng, mà cả hệ thống dựa vào đó.

    Không có ô "hàng lẻ": `lẻ = đã làm ra − Σ(thùng × quy cách)` suy ra được. Và nó
    KHÔNG phải `qty_short` — thiếu là chưa làm ra được, lẻ là làm rồi chưa đủ thùng.
    """

    work_date: date
    slot_hour: int = Field(ge=0, le=23, description="Khung giờ bắt đầu, 0-23")
    boxes: int = Field(gt=0, description="Số thùng ĐẦY đóng được trong khung giờ đó")
    note: NoteText | None = None


class PackingHourlyOut(BaseModel):
    """Trả về kèm hai con số dẫn xuất để màn hình khỏi tự tính lại."""

    boxes: int
    pcs_per_box: int
    packed_pcs: int = Field(description="Σ thùng × quy cách của CẢ VÒNG, quy ra pcs")
    made_pcs: int = Field(description="Số đã làm ra: SL đạt, hoặc Σ sản lượng giờ nếu chưa chốt")
    le_pcs: int = Field(description="Hàng lẻ còn trên bàn — KHÔNG phải hàng thiếu")
    message: str
