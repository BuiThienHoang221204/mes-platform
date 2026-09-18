"""Màn hình QC — bước 2."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.common.schemas import ReasonText


class QcDecideIn(BaseModel):
    """FAIL bắt buộc có lý do — CHECK `qc_fail_needs_reason` ở DB canh."""

    result: Literal["PASS", "FAIL"]
    reason_code_id: int | None = Field(default=None, description="Chọn từ danh mục để thống kê")
    reason_text: ReasonText | None = Field(default=None, description="Nguyên văn người kiểm ghi")


class QcOut(BaseModel):
    """FAIL thì MO về KHO và mở vòng mới — FE phải báo rõ chỗ này.

    Không về Bàn team leader: setup sai mà cho về Bàn team leader thì MO nhảy qua luôn Setup và QC,
    hàng lỗi đi thẳng vào chuyền mà không ai sửa máy (BRD §5).
    """

    result: str
    new_round_no: int | None = None
    message: str
