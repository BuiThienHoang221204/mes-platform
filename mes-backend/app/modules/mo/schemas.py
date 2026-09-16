"""Màn hình Kế hoạch: tạo lẻ · nhập CSV · Submit · huỷ."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.common.schemas import MoCode


class MoCreateIn(BaseModel):
    code: MoCode
    product_name: str
    quantity: int = Field(gt=0)
    required_production_min: int = Field(gt=0, description="TG yêu cầu Step4, tính bằng phút")
    pcs_per_box: int = Field(
        default=0, ge=0,
        description="Quy cách: bao nhiêu pcs một thùng. 0 = mặt hàng không đóng thùng",
    )


class MoImportIn(BaseModel):
    csv: str = Field(description="4 cột: Mã, Tên con hàng, Số lượng, TG yêu cầu (phút)")


class MoCancelIn(BaseModel):
    """§4A — nhập sai sau Submit thì huỷ kèm lý do rồi tạo lệnh mới, không sửa, không xoá."""

    reason: str = Field(min_length=1)


class MoOut(BaseModel):
    code: str
    product_name: str
    quantity: int
    pcs_per_box: int
    unit: str
    status: str
    required_production_sec: int
