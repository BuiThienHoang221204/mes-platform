"""DTO của màn hình đăng nhập và cấp token thiết bị."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.common.schemas import EmployeeCode, Pin, StationNo


class LoginIn(BaseModel):
    emp_code: EmployeeCode = Field(examples=["NV030"])
    pin: Pin


class SessionOut(BaseModel):
    """Phiên đăng nhập. KHÔNG chứa token — token nằm trong cookie httpOnly.

    FE không cần cầm token: trình duyệt tự gửi cookie kèm mọi request. Access hết
    hạn sau 15 phút thì gọi `POST /v1/auth/refresh`, cookie được ghi đè tại chỗ.
    """

    full_name: str
    roles: list[str]


class StationTokenOut(BaseModel):
    """Token gắn vào THIẾT BỊ, không phải vào người.

    Trạm lấy từ thiết bị chứ không lấy từ body — BRD §1b.3: mã QR chỉ nói MO nào,
    không nói bước nào. Để client tự khai trạm thì một máy giả được mọi trạm.
    """

    station: StationNo
    token: str
