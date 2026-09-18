"""AI đang thao tác, và người đó được làm gì ở trạm nào.

`Actor.require_step` là nơi THI HÀNH quyết định (PEP). Luật thì nằm trọn trong
`permissions.py` cạnh đây (PDP) — file này chỉ hỏi, không suy luận. Muốn đổi luật
thì sửa đúng file kia.

BRD §1b.3: "mã QR chỉ nói MO nào, không nói bước nào" — bước suy từ VAI của người
quét, xem `scan_station`. Người vận hành cầm điện thoại của mình đi qua nhiều trạm
nên không suy được từ thiết bị; nhưng vai thì đi theo người, và `require_station`
vẫn là nơi chặn cuối.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.common.errors import Forbidden, Invalid
from app.common.security.permissions import FULL, VIEW, full_stations, permission_for
from app.common.vocab.enums import STEP_NAMES
from app.common.vocab.error_codes import Err


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

    def scan_station(self, asked: int | None) -> int:
        """Quét này ăn vào trạm nào.

        Khai rõ thì lấy theo khai — `require_station` ngay sau đó chặn nếu người này
        không có quyền ở đó. Không khai mà chỉ làm được một trạm thì khỏi phải hỏi:
        §1b chốt quét là một thao tác, không có nút bấm nào chen giữa.
        """
        if asked is not None:
            return asked
        own = full_stations(self.roles)
        if len(own) == 1:
            return own[0]
        if not own:
            raise Forbidden(f"{self.full_name} không thao tác được ở trạm nào")
        names = ", ".join(STEP_NAMES[s] for s in own)
        raise Invalid(
            f"{self.full_name} làm được nhiều trạm ({names}) — chọn trạm trước khi quét",
            code=Err.SCAN_STATION,
        )

    def require_station(self, station_no: int) -> None:
        """Quét QR tại một trạm — cần quyền THAO TÁC ở trạm đó.

        Bàn team leader quét được ở trạm 4 (full quyền §9b.4), PLANNER quét được mọi trạm.
        """
        self.require_step(station_no, FULL)
