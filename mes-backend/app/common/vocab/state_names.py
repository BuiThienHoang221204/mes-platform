"""MỌI nhãn `from_state` / `to_state` của nhật ký `mo_event`, một chỗ duy nhất.

Cặp cột này đi thẳng lên màn hình Truy vết — `board/service.py` trả `from` và `to`
cho FE hiện nguyên văn. Nên đây là **chữ cho người vận hành đọc**, không phải mã
hợp đồng với FE: mã nằm ở cột `action` (`action_codes.py`).

Cặp cột ấy chở HAI vốn từ khác hẳn nhau, cố ý:

    Dòng vòng đời LỆNH     mã trạng thái — `MoStatus.DRAFT` → `MoStatus.PROCESSING`
    Dòng dưới XƯỞNG        nhãn tiếng Việt — "Chờ xử lý" → "Đang lắp ráp"

Không gộp làm một, vì dòng vòng đời lệnh phải khớp đúng giá trị ENUM dưới CSDL để
tra ngược được; còn dòng dưới xưởng thì thợ đọc, chẳng ai tra "PROCESSING" cả.

Ba nguồn nhãn, dùng đúng nguồn chứ đừng gõ lại:

    STEP_NAMES[n]      tên sáu trạm — `enums.py`, dùng chung với hàng đợi và câu lỗi
    MoStatus.X         trạng thái lệnh — `enums.py`, khớp ENUM dưới CSDL
    State.X            phần còn lại — file này

Trước đây bốn nhãn ở đây gõ tay lệch với `STEP_NAMES`: "Kho" và "Kho xuất",
"Nhập kho" và "Kho nhập" — cùng một trạm, hai lối viết, cùng hiện trên một bảng.
Giờ các chỗ đó gọi thẳng `STEP_NAMES`.
"""

from __future__ import annotations

from enum import StrEnum


class State(StrEnum):
    """Nhãn trạng thái dưới xưởng. Giá trị là TIẾNG VIỆT vì nó hiện lên màn hình."""

    # ══ Trạm 4 — bám theo `SegmentKind`: WAIT là chờ, RUN là đang lắp ═══════
    WAITING = "Chờ xử lý"
    ASSEMBLING = "Đang lắp ráp"

    # ══ Đóng thùng — nằm TRONG trạm 4 ═════════════════════════════════════════
    PACKING = "Đóng thùng"

    # ══ Chốt một chặng ══════════════════════════════════════════════════════
    FINISHED = "Hoàn thành"
    AWAITING_WAITING_DESK = "Chờ Bàn team leader nhận"   # QC PASS xong, chờ Bàn team leader quét

    # ══ Sang vòng mới — hai đích duy nhất (BRD §6b.1) ═══════════════════════
    NEW_ROUND_AT_WAREHOUSE = "Kho (vòng mới)"        # QC FAIL, làm lại từ gốc
    NEW_ROUND_AT_WAITING_DESK = "Bàn team leader (vòng mới)"  # thiếu SL, máy vẫn đúng


def round_label(round_no: int) -> str:
    """Nhãn một vòng chạy: `Vòng 2`. Dùng cho dòng mở vòng và dòng chuyển vòng."""
    return f"Vòng {round_no}"
