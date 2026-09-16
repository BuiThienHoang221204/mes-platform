"""AI đang thao tác, và người đó được làm gì ở trạm nào.

`Actor.require_step` là nơi THI HÀNH quyết định (PEP). Luật thì nằm trọn trong
`permissions.py` cạnh đây (PDP) — file này chỉ hỏi, không suy luận. Muốn đổi luật
thì sửa đúng file kia.

BRD §1b.3: "mã QR chỉ nói MO nào, không nói bước nào" — bước lấy từ THIẾT BỊ, xem
`require_station`. Để client tự khai trạm trong body thì một máy giả được mọi trạm.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.common.errors import Forbidden
from app.common.security.permissions import FULL, VIEW, permission_for
from app.common.vocab.enums import STEP_NAMES


@dataclass(frozen=True)
class Actor:
    """Người đang bấm. `roles` là mảng — một người giữ được nhiều vai."""

    user_id: str
    full_name: str
    roles: tuple[str, ...]

    def require_role(self, role: str) -> None:
        """Kiểm theo VAI. Chỉ dùng cho PLANNER — việc điều độ không gắn với trạm nào."""
        if role not in self.roles:
            raise Forbidden(f"{self.full_name} không có vai {role} — không thao tác ở đây được")

    def require_step(self, step_no: int, level: str = FULL) -> None:
        """Kiểm theo TRẠM — nơi thi hành quyết định của `permission_for`.

        Hai câu lỗi tách riêng: "không thuộc phòng ban" và "chỉ được xem" là hai
        tình huống khác hẳn, gộp một câu thì người ở xưởng không biết đi hỏi ai.
        """
        granted = permission_for(self.roles, step_no)
        if granted is None:
            raise Forbidden(
                f"{self.full_name} không thuộc phòng ban của {STEP_NAMES[step_no]}"
            )
        if level == FULL and granted == VIEW:
            raise Forbidden(
                f"{self.full_name} chỉ được XEM {STEP_NAMES[step_no]}, không thao tác được"
            )

    def require_station(self, station_no: int) -> None:
        """Quét QR tại một trạm — cần quyền THAO TÁC ở trạm đó.

        Bàn team leader quét được ở trạm 4 (full quyền §9b.4), PLANNER quét được mọi trạm.
        """
        self.require_step(station_no, FULL)
