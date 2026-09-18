"""Lỗi nghiệp vụ + dịch lỗi Postgres thành câu người vận hành đọc được.

Nguyên tắc ①: luật nằm trong CHECK / EXCLUDE / RULE của DB — backend KHÔNG kiểm lại
rồi mới ghi, mà ghi rồi dịch lỗi. Một bảng ánh xạ duy nhất ở đây.
"""

from __future__ import annotations

import re

from sqlalchemy.exc import IntegrityError, ProgrammingError

from app.common.vocab.error_codes import Err


class DomainError(Exception):
    """Lỗi nghiệp vụ — luôn kèm câu tiếng Việt cho người vận hành."""

    def __init__(self, message: str, *, code: str = Err.DOMAIN, status: int = 409) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status = status


class NotFound(DomainError):
    def __init__(self, message: str, *, code: str = Err.NOT_FOUND) -> None:
        super().__init__(message, code=code, status=404)


class Invalid(DomainError):
    """Dữ liệu vào sai — thiếu lý do, số âm, mã sai định dạng…"""

    def __init__(self, message: str, *, code: str = Err.INVALID) -> None:
        super().__init__(message, code=code, status=422)


class Forbidden(DomainError):
    """KHÔNG ĐỦ QUYỀN — danh tính hợp lệ nhưng không được làm việc này.

    Lấy token mới cũng vô ích, nên client phải KHÔNG refresh khi gặp lỗi này.
    """

    def __init__(self, message: str, *, code: str = Err.FORBIDDEN) -> None:
        super().__init__(message, code=code, status=403)


class Unauthenticated(DomainError):
    """CHƯA XÁC THỰC — thiếu token, token hỏng, hoặc token hết hạn.

    Phải là 401 chứ không phải 403. Trình duyệt chỉ đổi refresh lấy access mới khi
    thấy 401; trả 403 thì sau 15 phút mọi lời gọi đều hỏng trong khi refresh token
    còn sống bảy ngày mà không ai dùng tới.
    """

    def __init__(self, message: str, *, code: str = Err.UNAUTHENTICATED) -> None:
        super().__init__(message, code=code, status=401)


# ── Tên ràng buộc trong DB → (mã, HTTP, câu thông báo) ──────────────────────
# Câu chữ lấy đúng như demo để người vận hành không phải học lại.
CONSTRAINT_MESSAGES: dict[str, tuple[str, int, str]] = {
    "mo_code_format": (Err.MO_CODE, 422, "Mã MO phải là chữ M kèm đúng 6 chữ số, ví dụ M068820"),
    "manufacturing_order_code_key": (Err.MO_DUPLICATE, 409, "Mã MO này đã có trong hệ thống"),
    "mo_cancel_needs_reason": (Err.CANCEL_REASON, 422, "Huỷ lệnh bắt buộc ghi lý do"),
    "mo_round_one_open": (Err.ROUND_OPEN, 409, "MO này đã có một vòng đang chạy"),
    "mo_round_mo_id_round_no_key": (Err.ROUND_DUP, 409, "Vòng này đã tồn tại"),
    "mo_step_round_id_step_no_key": (Err.STEP_DUP, 409, "Bước này đã được nhận ở vòng hiện tại"),
    "step_closed_after_accept": (Err.STEP_TIME, 422, "Mốc đóng bước không được sớm hơn mốc nhận"),
    "qc_fail_needs_reason": (Err.QC_REASON, 422, "QC không đạt — bắt buộc ghi lý do"),
    "prod_has_output": (Err.PROD_EMPTY, 422,
                        "Vòng này chưa làm ra PCS nào — không có gì để chốt sổ"),
    "ng_needs_reason": (Err.NG_REASON, 422, "Có hàng hỏng — bắt buộc ghi LÝ DO HỎNG"),
    "short_needs_reason": (Err.SHORT_REASON, 422, "Làm thiếu — bắt buộc ghi LÝ DO THIẾU"),
    "production_no_update": (Err.PROD_CLOSED, 409, "Vòng này đã chốt sổ Sản xuất rồi"),
    "production_pkey": (Err.PROD_CLOSED, 409, "Vòng này đã chốt sổ Sản xuất rồi"),
    "pack_done_consistent": (Err.PACK_STATE, 422, "Kết thúc đóng thùng phải kèm SL đã đóng"),
    "packing_pkey": (Err.PACK_STARTED, 409, "Vòng này đã bắt đầu đóng thùng rồi"),
    "warehouse_in_pkey": (Err.WAREHOUSE_IN_DONE, 409, "Vòng này đã nhập kho rồi"),
    "seg_ends_after_start": (Err.SEG_TIME, 422, "Mốc kết thúc đoạn phải sau mốc bắt đầu"),
    "seg_reason_only_on_wait": (Err.SEG_REASON, 422, "Lý do dừng chỉ gắn với đoạn chờ"),
    "seg_one_open": (Err.SEG_OPEN, 409, "Chuyền này đang có một đoạn chưa đóng ở vòng hiện tại"),
    "hourly_output_round_id_work_date_slot_hour_key": (
        Err.HOURLY_DUP,
        409,
        "Khung giờ này của ngày đó đã ghi rồi — mỗi khung mỗi ngày chỉ ghi một lần",
    ),
    "hourly_output_qty_check": (Err.HOURLY_QTY, 422, "Sản lượng giờ phải lớn hơn 0"),
    "packing_hourly_round_id_work_date_slot_hour_key": (
        Err.BOX_DUP,
        409,
        "Khung giờ này của ngày đó đã ghi thùng rồi — mỗi khung mỗi ngày một lần",
    ),
    "line_code_key": (Err.LINE_DUPLICATE, 409, "Mã chuyền này đã có trong hệ thống"),
    "line_segment_line_id_fkey": (
        Err.LINE_IN_USE,
        409,
        "Chuyền này đã có lịch sử chạy — không xoá được. Hãy TẮT nó thay vì xoá",
    ),
}

# Trigger RAISE EXCEPTION — bắt theo đầu câu, giữ nguyên nội dung vì nó đã có số liệu
TRIGGER_PREFIXES: dict[str, tuple[str, int]] = {
    "Đạt ": (Err.PROD_BALANCE, 409),
    # "Đã đóng " phải đứng TRƯỚC "Đóng " — nếu không thì… thực ra không sao, vì
     # `str.startswith` so từ đầu chuỗi và "Đã đóng…" không bắt đầu bằng "Đóng ".
     # Giữ hai dòng cạnh nhau để lần sau sửa còn nhìn thấy nhau.
    "Đã đóng ": (Err.BOX_OVER_MADE, 409),
    "Đóng ": (Err.PACK_OVER_OK, 409),
    "Vòng chưa chốt sổ SX": (Err.PACK_BEFORE_PROD, 409),
    "MO ": (Err.MO_LOCKED, 409),
    "Σ sản lượng giờ": (Err.HOURLY_OVER, 409),
}

_CONSTRAINT_RE = re.compile(r'constraint "([^"]+)"')


def translate_db_error(exc: Exception) -> DomainError | None:
    """Đổi lỗi Postgres thành DomainError. Trả None nếu không nhận ra."""
    orig = getattr(exc, "orig", None)
    text = str(orig) if orig is not None else str(exc)

    if isinstance(exc, IntegrityError | ProgrammingError) or orig is not None:
        # 1. Ràng buộc có tên
        name = getattr(getattr(orig, "diag", None), "constraint_name", None)
        if not name:
            m = _CONSTRAINT_RE.search(text)
            name = m.group(1) if m else None
        if name and name in CONSTRAINT_MESSAGES:
            code, status, msg = CONSTRAINT_MESSAGES[name]
            return DomainError(msg, code=code, status=status)

        # 2. Trigger tự RAISE — câu đã có số liệu, giữ nguyên
        first = text.strip().splitlines()[0]
        first = first.split("\n")[0].removeprefix("(psycopg.errors.RaiseException) ").strip()
        for prefix, (code, status) in TRIGGER_PREFIXES.items():
            if first.startswith(prefix):
                return DomainError(first, code=code, status=status)
    return None
