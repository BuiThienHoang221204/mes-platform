"""Kiểu liệt kê — khớp đúng tên ENUM trong Postgres (DB-GON §1)."""

from __future__ import annotations

from enum import StrEnum


class MoStatus(StrEnum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class QcVerdict(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"


class SegmentKind(StrEnum):
    WAIT = "WAIT"   # chờ xử lý — TG chờ
    RUN = "RUN"     # đang lắp ráp — TG thực tế


class ReasonGroup(StrEnum):
    HOLD = "HOLD"      # dừng máy
    NG = "NG"          # hàng hỏng
    SHORT = "SHORT"    # làm thiếu
    QC = "QC"          # QC không đạt
    PACKING = "PACKING"


# Sáu trạm. Bàn team leader (3) và Setup (1) không sinh dữ liệu riêng ngoài giờ giấc.
STEP_NAMES = {
    0: "Kho xuất",      # kho vật tư — giao hàng XUỐNG xưởng
    1: "Setup máy",
    2: "QC",
    3: "Bàn team leader",
    4: "Sản xuất",
    5: "Kho nhập",      # kho thành phẩm — nhận hàng TỪ xưởng lên
}

# Vòng mới quay về đâu — chỉ có đúng hai đích (BRD §6b.1)
RETURN_TO_KHO = 0       # QC FAIL: setup sai, phải làm lại từ gốc
RETURN_TO_BANCHO = 3    # thiếu SL / dừng quá lâu: máy vẫn đúng, chỉ chưa đủ số
