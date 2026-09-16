"""MỌI `action` ghi vào nhật ký `mo_event`, một chỗ duy nhất.

`mo_event` là sổ CHỈ-GHI-THÊM — RULE ở CSDL chặn UPDATE và DELETE, nên một chuỗi
gõ sai nằm lại đó vĩnh viễn, không ai sửa được nữa. Đó là khác biệt lớn nhất so
với `error_codes.py`: mã lỗi gõ sai thì FE hiện nhầm màn hình một lần rồi thôi,
còn `action` gõ sai thì hỏng vĩnh viễn phần truy cứu của MO đó.

    event_repo.log(db, ..., action=Act.MO_SUBMIT)   ← gõ sai là AttributeError ngay

Cột `mo_event.action` là `text` trần, không có CHECK — CSDL nhận mọi chuỗi. Nên
lớp canh duy nhất là file này cộng `tests/test_action_codes.py`.

Vốn từ lấy theo BRD §"Nhật ký". Ba chỗ bản BRD ghi khác mã nguồn, cố ý:

    KHO_ACCEPT              → mã nguồn phát `STEP0_ACCEPT`, cho đồng bộ với năm
                              trạm còn lại. Trạm 0 không có lý do gì phải khác.
    STEP_N_AUTO_COMPLETE    → không phát. Bước trước tự đóng khi trạm sau quét
                              nhận, và việc đó đã nằm trong chính dòng
                              `STEP{n}_ACCEPT` — ghi thêm một dòng là ghi hai lần
                              cùng một sự việc.
    STEP4_COMPLETE          → không phát; `STEP4_FINISH_ALL` là dòng chốt trạm 4.

Ngược lại `ROUND_OPEN` có trong mã nguồn mà BRD chưa liệt kê.
"""

from __future__ import annotations

from enum import StrEnum


class Act(StrEnum):
    """Hành động ghi vào nhật ký. Giá trị = tên, để đọc sổ thấy ngay là dòng gì."""

    # ══ Vòng đời một lệnh ═══════════════════════════════════════════════════
    MO_CREATE = "MO_CREATE"                 # tạo lệnh, trạng thái DRAFT
    MO_SUBMIT = "MO_SUBMIT"                 # chốt lệnh + mở vòng 1 (§4A)
    MO_CANCEL = "MO_CANCEL"                 # huỷ kèm lý do (§2.3)
    MO_PARTIAL = "MO_PARTIAL"               # nhập kho thiếu — còn phần dư
    MO_COMPLETE = "MO_COMPLETE"             # đủ SL, đóng đơn

    # ══ Vòng chạy ═══════════════════════════════════════════════════════════
    ROUND_OPEN = "ROUND_OPEN"               # mở một vòng mới
    RETURN_KHO = "RETURN_KHO"               # vòng sau bắt đầu lại từ Kho
    RETURN_BANCHO = "RETURN_BANCHO"         # vòng sau vào thẳng Bàn team leader (§6b.2)

    # ══ Quét nhận ở sáu trạm — xem `step_accept()` ══════════════════════════
    STEP0_ACCEPT = "STEP0_ACCEPT"           # Kho xuất
    STEP1_ACCEPT = "STEP1_ACCEPT"           # Setup
    STEP2_ACCEPT = "STEP2_ACCEPT"           # QC
    STEP3_ACCEPT = "STEP3_ACCEPT"           # Bàn team leader
    STEP4_ACCEPT = "STEP4_ACCEPT"           # Sản xuất
    STEP5_ACCEPT = "STEP5_ACCEPT"           # Kho nhập

    # ══ Trạm 0 — Kho xuất ═══════════════════════════════════════════════════
    KHO_HANDOVER = "KHO_HANDOVER"           # bàn giao vật tư cho Setup

    # ══ Trạm 2 — QC ═════════════════════════════════════════════════════════
    QC_PASS = "QC_PASS"
    QC_FAIL = "QC_FAIL"                     # kèm lý do (§5)

    # ══ Trạm 4 — Sản xuất ═══════════════════════════════════════════════════
    RUN_ADD = "RUN_ADD"                     # gán chuyền vào vòng
    RUN_START = "RUN_START"                 # chuyền bắt đầu lắp ráp
    RUN_HOLD = "RUN_HOLD"                   # dừng máy kèm lý do (§17)
    HOURLY_ADD = "HOURLY_ADD"               # ghi sản lượng một khung giờ (§7.2b)
    STEP4_FINISH_ALL = "STEP4_FINISH_ALL"   # chốt sổ sản xuất cả vòng

    # ══ Đóng thùng — nằm TRONG trạm 4 ═════════════════════════════════════════
    PACK_START = "PACK_START"
    PACK_HOURLY = "PACK_HOURLY"             # ghi số thùng một khung giờ (§7b.2)
    PACK_COMPLETE = "PACK_COMPLETE"


def step_accept(step_no: int) -> Act:
    """Dòng nhật ký lúc trạm `step_no` quét nhận.

    Sáu hằng số khai riêng chứ không ghép chuỗi `f"STEP{n}_ACCEPT"` tại chỗ gọi:
    ghép chuỗi thì `step_no` lạc ra ngoài 0-5 vẫn ghi xuống sổ ngon lành, mà sổ
    này không xoá được. Tra bảng thì số lạ ném `KeyError` ngay tại chỗ.
    """
    try:
        return Act[f"STEP{step_no}_ACCEPT"]
    except KeyError:
        raise ValueError(f"Không có trạm {step_no} — chỉ có trạm 0 đến 5") from None
