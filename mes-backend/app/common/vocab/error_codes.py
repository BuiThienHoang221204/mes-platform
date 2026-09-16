"""MỌI mã lỗi của backend, một chỗ duy nhất.

Mã lỗi là **hợp đồng với frontend**: FE nhìn `code` để quyết định hiện màn hình nào,
chứ không đọc `message` (câu tiếng Việt có thể sửa lại bất cứ lúc nào). Nên đổi một
mã là phá FE — cứ coi như đổi tên một endpoint.

Tên mã dùng TIẾNG ANH và theo tên MODULE — `NO_WAREHOUSE_OUT_ACCEPT` chứ không
`NO_KHO_ACCEPT`, vì đây là thứ lộ ra ngoài (BE-PLAN §"Tên lộ ra ngoài thì tiếng Anh").
Bốn mã `NO_*_ACCEPT` cùng một nghĩa nên phải cùng một khuôn.

Trước đây 53 mã này nằm rải trong 10 file dưới dạng chuỗi trần `code="..."`. Gõ sai
một chữ thì FE nhận mã lạ mà backend không báo gì, vì chuỗi nào cũng hợp lệ.

    raise DomainError("...", code=Err.QC_DONE)      ← gõ sai là AttributeError ngay

`tests/test_error_codes.py` canh hai chiều: không còn chuỗi trần nào ngoài file này,
và mọi mã khai ở đây đều có nơi dùng.

Nhóm theo NƠI SINH RA, không theo mức nghiêm trọng:

    Chung          mặc định của bốn lớp lỗi
    Lệnh (mo)      vòng đời một lệnh trước khi xuống xưởng
    Bước / vòng    luật đi qua sáu trạm
    Từng trạm      kho xuất · QC · sản xuất · đóng thùng · kho nhập
    Từ CSDL        do CHECK / trigger / RULE ném ra, backend chỉ dịch lại
"""

from __future__ import annotations

from enum import StrEnum


class Err(StrEnum):
    """Mã lỗi. Giá trị = tên, để đọc log thấy ngay là mã nào."""

    # ══ Chung — mặc định của DomainError / NotFound / Invalid / Forbidden ════
    DOMAIN = "DOMAIN"
    NOT_FOUND = "NOT_FOUND"
    INVALID = "INVALID"
    FORBIDDEN = "FORBIDDEN"

    # ══ Lệnh sản xuất ═══════════════════════════════════════════════════════
    MO_CODE = "MO_CODE"                     # mã không đúng dạng M + 6 chữ số
    MO_DUPLICATE = "MO_DUPLICATE"           # trùng mã
    ALREADY_SUBMITTED = "ALREADY_SUBMITTED"  # Submit lần hai
    CANCEL_REASON = "CANCEL_REASON"         # huỷ mà không ghi lý do (§2.3)
    MO_LOCKED = "MO_LOCKED"                 # sửa sau Submit (§4A) — trigger ném

    # ══ Vòng chạy và bước ═══════════════════════════════════════════════════
    ROUND_OPEN = "ROUND_OPEN"               # MO đã có một vòng đang mở
    ROUND_DUP = "ROUND_DUP"
    STEP_DUP = "STEP_DUP"                   # trạm này đã quét nhận rồi
    STEP_TIME = "STEP_TIME"                 # mốc đóng sớm hơn mốc nhận
    STEP_DONE = "STEP_DONE"
    SKIP_STEP = "SKIP_STEP"                 # quét nhảy cóc qua trạm chưa xong

    # ── Chưa xong việc ở trạm trước, trạm sau không nhận được ───────────────
    NO_HANDOVER = "NO_HANDOVER"             # Kho chưa bàn giao
    NO_QC = "NO_QC"                         # chưa có kết quả QC
    QC_FAILED = "QC_FAILED"                 # QC FAIL, không đi tiếp được
    NO_PRODUCTION = "NO_PRODUCTION"         # chưa chốt sổ sản xuất
    NO_PACKING = "NO_PACKING"               # chưa kết thúc đóng thùng

    # ══ Trạm 0 — Kho xuất ═══════════════════════════════════════════════════
    NO_WAREHOUSE_OUT_ACCEPT = "NO_WAREHOUSE_OUT_ACCEPT"   # chưa quét nhận ở trạm 0
    HANDED_OVER = "HANDED_OVER"             # đã bàn giao rồi

    # ══ Trạm 2 — QC ═════════════════════════════════════════════════════════
    NO_QC_ACCEPT = "NO_QC_ACCEPT"                   # chưa quét nhận ở trạm 2
    QC_DONE = "QC_DONE"                     # vòng này đã có kết quả
    QC_REASON = "QC_REASON"                 # FAIL mà không có lý do (§5)

    # ══ Trạm 4 — Sản xuất ═══════════════════════════════════════════════════
    NO_PRODUCTION_ACCEPT = "NO_PRODUCTION_ACCEPT"   # chưa quét nhận ở trạm 4
    NO_LINE = "NO_LINE"                     # chuyền chưa gán vào vòng
    LINE_ADDED = "LINE_ADDED"               # chuyền đã có trong vòng
    LINE_RUNNING = "LINE_RUNNING"           # đang chạy rồi
    LINE_NOT_RUNNING = "LINE_NOT_RUNNING"   # không đang chạy, không dừng được
    LINE_NOT_RUN = "LINE_NOT_RUN"
    LINE_BUSY = "LINE_BUSY"                 # chuyền chạy MO khác cùng khung giờ
    LINE_IN_USE = "LINE_IN_USE"             # xoá chuyền đã có lịch sử chạy
    LINE_DUPLICATE = "LINE_DUPLICATE"       # thêm chuyền trùng mã
    HOLD_REASON = "HOLD_REASON"             # dừng máy mà không ghi lý do (§17)
    SEG_TIME = "SEG_TIME"                   # mốc kết thúc đoạn không sau mốc bắt đầu
    SEG_REASON = "SEG_REASON"               # lý do dừng gắn nhầm vào đoạn chạy
    SEG_OPEN = "SEG_OPEN"                   # chuyền còn một đoạn chưa đóng

    # ── Chốt sổ sản xuất ────────────────────────────────────────────────────
    PROD_EMPTY = "PROD_EMPTY"               # chưa làm ra PCS nào
    PROD_CLOSED = "PROD_CLOSED"             # đã chốt sổ rồi
    PROD_BALANCE = "PROD_BALANCE"           # đạt+hỏng+thiếu ≠ mục tiêu — trigger ném
    NG_REASON = "NG_REASON"                 # có hàng hỏng mà không ghi lý do
    SHORT_REASON = "SHORT_REASON"           # làm thiếu mà không ghi lý do

    # ── Sản lượng theo giờ ──────────────────────────────────────────────────
    NOT_RUNNING = "NOT_RUNNING"             # không có chuyền nào đang chạy
    HOURLY_DUP = "HOURLY_DUP"               # khung giờ đó của ngày đó ghi rồi
    HOURLY_QTY = "HOURLY_QTY"               # sản lượng phải lớn hơn 0
    HOURLY_OVER = "HOURLY_OVER"             # tổng vượt mục tiêu vòng — trigger ném
    HOURLY_PEOPLE = "HOURLY_PEOPLE"         # thiếu số người đứng chuyền
    HOURLY_TARGET = "HOURLY_TARGET"         # thiếu sản lượng yêu cầu của khung

    # ══ Đóng thùng — nằm TRONG trạm 4 ═════════════════════════════════════════
    NO_RUN = "NO_RUN"                       # chưa chuyền nào chạy (§7b)
    PACK_STARTED = "PACK_STARTED"           # đã bắt đầu đóng thùng rồi
    NO_PACK = "NO_PACK"                     # chưa bắt đầu, không kết thúc được
    PACK_DONE = "PACK_DONE"                 # đã kết thúc rồi
    PACK_STATE = "PACK_STATE"               # kết thúc mà thiếu SL đã đóng
    PACK_OVER_OK = "PACK_OVER_OK"           # đóng vượt SL đạt — trigger ném
    PACK_BEFORE_PROD = "PACK_BEFORE_PROD"   # kết thúc trước khi chốt sổ sản xuất

    # ── Đếm thùng theo giờ (§7b.2) ──────────────────────────────────────────
    NO_PCS_PER_BOX = "NO_PCS_PER_BOX"       # MO chưa khai quy cách, không đếm thùng được
    BOX_DUP = "BOX_DUP"                     # khung giờ đó của ngày đó ghi thùng rồi
    BOX_OVER_MADE = "BOX_OVER_MADE"         # đóng nhiều hơn số đã làm ra — trigger ném

    # ══ Trạm 5 — Kho nhập ═══════════════════════════════════════════════════
    NO_WAREHOUSE_IN_ACCEPT = "NO_WAREHOUSE_IN_ACCEPT"     # chưa quét nhận ở trạm 5
    WAREHOUSE_IN_DONE = "WAREHOUSE_IN_DONE"         # vòng này đã nhập kho rồi

    # ══ Quét QR ═════════════════════════════════════════════════════════════
    SCAN_READ = "SCAN_READ"                 # đầu đọc trả chuỗi không đọc được

    # ══ Chỉ CSDL ném ra ═════════════════════════════════════════════════════
    DB = "DB"                               # lỗi CSDL không nhận ra được
