"""Payload màn hình Sản xuất — gán chuyền · chạy · dừng · chốt sổ · sản lượng giờ."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field

from app.common.schemas import NoteText, ReasonText

_LINE_CODE = Field(examples=["L02"], pattern=r"^L\d{2}$")


class LineAssignIn(BaseModel):
    """Thêm chuyền vào vòng. TG CHỜ của chuyền bắt đầu đếm từ đây."""

    line_code: str = _LINE_CODE


class LineStartIn(BaseModel):
    """Cho chuyền chạy. TG CHỜ chốt lại, TG THỰC TẾ bắt đầu đếm."""

    line_code: str = _LINE_CODE


class LineHoldIn(BaseModel):
    """Bấm dừng. §17 — BẮT BUỘC ghi lý do, ít nhất một trong hai ô."""

    line_code: str = _LINE_CODE
    reason_code_id: int | None = None
    reason_text: ReasonText | None = None


class ProductionCloseIn(BaseModel):
    """Chốt sổ Sản xuất — ba số và hai lý do.

    Ba số phải cộng ĐÚNG BẰNG mục tiêu vòng. Không kiểm ở đây: trigger
    `production_balances` lo, và nó đúng cả khi có người ghi thẳng vào DB.

    Hai lý do hỏi RIÊNG vì là hai chuyện khác nhau — hỏng 500 vì lỗi khuôn,
    thiếu 1.000 vì chờ bù liệu. Gộp một ô thì mất một nửa thông tin.
    """

    qty_ok: int = Field(ge=0, description="ĐẠT — con số duy nhất cộng vào tiến độ MO")
    qty_ng: int = Field(ge=0, description="HỎNG — làm ra rồi nhưng hỏng")
    qty_short: int = Field(ge=0, description="THIẾU — không làm ra được")
    ng_reason_code_id: int | None = None
    ng_reason_text: ReasonText | None = None
    short_reason_code_id: int | None = None
    short_reason_text: ReasonText | None = None


class HourlyIn(BaseModel):
    """BA số mỗi khung giờ, cả ba bắt buộc (§7.2b).

    Một mình `qty` không trả lời được câu duy nhất người quản lý cần hỏi — *giờ vừa
    rồi chạy tốt hay không*. 500 cái với 8 người là khá, với 20 người là có vấn đề;
    định mức 400 thì 500 là vượt, định mức 700 thì 500 là hụt.

    `Đạt %` và `Năng suất` KHÔNG có ở đây: chúng suy ra được từ ba số trên, cho nhập
    tay là mở đường cho số liệu tự mâu thuẫn.

    Mỗi (vòng, ngày, khung giờ) chỉ một dòng — partial unique index ở DB canh.

    Tổng các dòng này phải khớp `qty_ok` của vòng khi chốt sổ; lệch thì bảng
    chi tiết vòng chạy hiện cảnh báo chứ không chặn, vì người nhập giờ và người
    chốt sổ là hai người khác nhau.
    """

    work_date: date
    slot_hour: int = Field(ge=0, le=23, description="Khung giờ bắt đầu, 0-23")
    headcount: int = Field(gt=0, description="Số người đứng chuyền khung giờ đó")
    target_qty: int = Field(gt=0, description="Sản lượng YÊU CẦU của khung giờ đó")
    qty: int = Field(gt=0, description="Sản lượng THỰC TẾ làm ra")
    note: NoteText | None = None
