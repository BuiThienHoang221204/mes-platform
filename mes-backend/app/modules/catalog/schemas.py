"""Danh mục chỉ-đọc cho các ô chọn của FE: chuyền và mã lý do."""

from __future__ import annotations

from pydantic import BaseModel, Field


class CatalogLine(BaseModel):
    id: int
    code: str
    name: str | None
    is_active: bool


class LineCreateIn(BaseModel):
    """Thêm chuyền. `id` KHÔNG nhận từ ngoài — máy chủ tự cấp số kế tiếp."""

    code: str = Field(pattern=r"^[A-Za-z0-9-]{1,10}$", examples=["L15"])
    name: str | None = Field(default=None, max_length=100)


class CatalogReason(BaseModel):
    """`group_code` để FE lọc: chỉ đưa lý do QC vào ô QC, lý do dừng vào ô dừng."""

    id: int
    group_code: str
    name: str
    is_active: bool
