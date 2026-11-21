"""Kiểu liệt kê — khớp đúng tên ENUM trong Postgres (DB-GON §1)."""

from __future__ import annotations

from enum import StrEnum


class MoStatus(StrEnum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class SegmentKind(StrEnum):
    WAIT = "WAIT"   # chờ xử lý — TG chờ
    RUN = "RUN"     # đang lắp ráp — TG thực tế


class ReasonGroup(StrEnum):
    HOLD = "HOLD"      # dừng máy
    NG = "NG"          # hàng hỏng
    SHORT = "SHORT"    # làm thiếu
    PACKING = "PACKING"


# Năm trạm. Bàn team leader (2) và Setup (1) không sinh dữ liệu riêng ngoài giờ giấc.
STEP_NAMES = {
    0: "Kho xuất",          # kho vật tư — giao hàng XUỐNG xưởng
    1: "Setup máy",
    2: "Bàn team leader",
    3: "Sản xuất",
    4: "Kho nhập",          # kho thành phẩm — nhận hàng TỪ xưởng lên
}

# Trạm có hàng chờ dựng TRỰC TIẾP từ bước của trạm liền trước:
# Bàn team leader (2) đợi Setup máy (1), Sản xuất (3) đợi Bàn team leader (2).
# Hai trạm còn lại vào hàng chờ theo điều kiện khác: Setup máy đợi Kho bàn giao, Kho nhập đợi đóng thùng xong.
QUEUE_WAITS_ON_PREV_STEP = frozenset({2, 3})

# Vòng mới quay về đâu (BRD §6b.1)
RETURN_TO_KHO = 0
RETURN_TO_BANCHO = 2    # thiếu SL / dừng quá lâu: vào thẳng Bàn team leader
