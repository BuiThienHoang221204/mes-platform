"""Màn hình Kế hoạch: tạo lẻ · nhập tệp Excel · Submit · huỷ."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.common.schemas import MAX_IMPORT_ROWS, MoCode, Name, ReasonText


class MoCreateIn(BaseModel):
    code: MoCode
    product_name: Name
    quantity: int = Field(gt=0)
    required_production_min: int = Field(gt=0, description="TG yêu cầu Step4, tính bằng phút")
    pcs_per_box: int = Field(
        default=0, ge=0,
        description="Quy cách: bao nhiêu pcs một thùng. 0 = mặt hàng không đóng thùng",
    )


class MoExcelRowIn(BaseModel):
    """Một dòng trong tệp Excel, đã tách cột sẵn.

    Thời gian đi bằng GIÂY chứ không phải phút như `MoCreateIn`: cột
    `XA working hour` trong tệp là số thập phân, quy về phút rồi làm tròn là
    mất số lẻ ngay trước khi ghi xuống cột `required_production_sec`.
    """

    code: MoCode
    product_name: Name
    quantity: int = Field(gt=0)
    required_production_sec: int = Field(gt=0)
    pcs_per_box: int = Field(default=0, ge=0)


class MoExcelImportIn(BaseModel):
    items: list[MoExcelRowIn] = Field(min_length=1, max_length=MAX_IMPORT_ROWS)


class MoBatchIn(BaseModel):
    """Danh sách mã được tích chọn trên bảng Sổ lệnh."""

    codes: list[MoCode] = Field(min_length=1, max_length=MAX_IMPORT_ROWS)


class MoCancelBatchIn(MoBatchIn):
    reason: ReasonText


class MoCancelIn(BaseModel):
    """§4A — nhập sai sau Submit thì huỷ kèm lý do rồi tạo lệnh mới, không sửa, không xoá."""

    reason: ReasonText


class MoOut(BaseModel):
    code: str
    product_name: Name
    quantity: int
    pcs_per_box: int
    unit: str
    status: str
    required_production_sec: int
