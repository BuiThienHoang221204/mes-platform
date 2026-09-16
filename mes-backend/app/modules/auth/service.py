"""Luật đăng nhập: cấp cặp token, xoay vòng refresh, bắt token bị dùng lại.

    TokenPair                             access + refresh + thông tin người
    login(db, emp_code, pin)              kiểm PIN rồi cấp cặp token
    refresh(db, refresh_raw)              đổi refresh cũ lấy cặp mới — XOAY VÒNG
    logout(db, refresh_raw)               hạ refresh đang giữ

Refresh dùng ĐÚNG MỘT LẦN. Gửi lên lần hai nghĩa là có người giữ bản sao, và
không có cách nào biết bản sao nằm ở máy nào — nên `refresh` thu hồi CẢ CHUỖI
của người đó và bắt đăng nhập lại.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.common.clock import now
from app.common.errors import Forbidden
from app.common.security.tokens import hash_token, make_access_token, make_refresh_token, verify_pin
from app.common.uow import transactional
from app.modules.auth import repository as auth_repo
from app.modules.auth.models import AppUser, RefreshToken

# Một câu duy nhất cho mọi kiểu sai khi đăng nhập: sai mã, sai PIN, tài khoản đã
# tắt. Phân biệt ra là nói cho người dò biết mã nào có thật.
BAD_CREDENTIALS = "Sai mã nhân viên hoặc mã PIN"


@dataclass(frozen=True)
class TokenPair:
    access_token: str
    refresh_token: str
    full_name: str
    roles: list[str]


@transactional
def login(db: Session, *, emp_code: str, pin: str) -> TokenPair:
    """Kiểm mã nhân viên + PIN rồi cấp cặp token."""
    user = auth_repo.get_user_by_emp_code(db, emp_code)
    if user is None or not user.is_active or not user.pin_hash:
        raise Forbidden(BAD_CREDENTIALS)
    if not verify_pin(pin, user.pin_hash):
        raise Forbidden(BAD_CREDENTIALS)
    pair, _ = _issue_token_pair(db, user)
    return pair


def refresh(db: Session, *, refresh_raw: str) -> TokenPair:
    """Đổi refresh cũ lấy cặp mới. Đây là chỗ XOAY VÒNG và bắt dùng lại.

    KHÔNG gắn `@transactional`, và đó là chủ ý. Khi phát hiện dùng lại thì việc thu
    hồi phải được CHỐT LẠI, mà câu `raise` báo lỗi ngay sau đó lại huỷ chính giao
    dịch đang chứa nó. Nên việc thu hồi là một đơn vị công việc RIÊNG: commit xong
    rồi mới ném.

    Nhưng *phát hiện* thì nằm chung giao dịch với *xoay vòng* — cả hai dưới một lần
    khoá dòng. Tách ra thì hai request cầm cùng một token đều qua được bước kiểm rồi
    cùng xoay vòng, tức là phát hai cặp token hợp lệ từ một refresh.
    """
    pair = _rotate(db, refresh_raw)
    if pair is not None:
        return pair

    n = _revoke_chain(db, refresh_raw)
    raise Forbidden(f"Phiên đăng nhập đã bị dùng lại — đã thu hồi {n} phiên, đăng nhập lại")


@transactional
def _revoke_chain(db: Session, refresh_raw: str) -> int:
    """Thu hồi mọi phiên của chủ token. Đơn vị công việc riêng — xem `refresh`."""
    row = auth_repo.find_refresh(db, hash_token(refresh_raw))
    return auth_repo.revoke_all_for_user(db, row.user_id) if row is not None else 0


@transactional
def _rotate(db: Session, refresh_raw: str) -> TokenPair | None:
    """Xoay vòng. Trả **None** nghĩa là PHÁT HIỆN DÙNG LẠI — người gọi lo thu hồi.

    Không tự thu hồi ở đây: việc đó phải commit, mà hàm này thì người gọi sắp ném
    lỗi ngay sau. Trả về thay vì ném chính là cách giữ hai yêu cầu đó không đá nhau.
    """
    row = auth_repo.find_refresh(db, hash_token(refresh_raw))
    if row is None:
        raise Forbidden("Phiên đăng nhập không hợp lệ — đăng nhập lại")
    if row.used_at is not None:
        return None   # ← token này đã đổi rồi mà vẫn có người cầm được bản sao
    if row.revoked_at is not None:
        raise Forbidden("Phiên đăng nhập đã bị thu hồi — đăng nhập lại")
    if row.expires_at <= now():
        raise Forbidden("Phiên đăng nhập đã hết hạn — đăng nhập lại")

    user = auth_repo.get_user_by_id(db, row.user_id)
    if user is None or not user.is_active:
        raise Forbidden("Tài khoản không còn hiệu lực")

    fresh, moi = _issue_token_pair(db, user)
    row.used_at = now()
    row.replaced_by = moi.id
    db.flush()
    return fresh


@transactional
def logout(db: Session, *, refresh_raw: str) -> None:
    """Hạ refresh đang giữ. Access token còn sống tới khi hết hạn — tối đa 15 phút."""
    row = auth_repo.find_refresh(db, hash_token(refresh_raw))
    if row is not None and row.revoked_at is None:
        row.revoked_at = now()
        db.flush()


def _issue_token_pair(db: Session, user: AppUser) -> tuple[TokenPair, RefreshToken]:
    """Phát cặp token mới, trả kèm DÒNG refresh vừa ghi.

    Trả cả dòng vì người gọi cần `id` của nó để nối chuỗi xoay vòng. Tra lại bằng
    hash là thừa một câu `SELECT … FOR UPDATE` trên chính dòng vừa INSERT — thừa
    một vòng đi về CSDL và thừa một lần khoá, ở endpoint chạy 15 phút một lần trên
    mọi máy tính bảng.
    """
    raw, token_hash, expires_at = make_refresh_token()
    row = auth_repo.save_refresh(
        db, user_id=user.id, token_hash=token_hash, expires_at=expires_at
    )
    pair = TokenPair(
        access_token=make_access_token(user.id),
        refresh_token=raw,
        full_name=user.full_name,
        roles=list(user.roles),
    )
    return pair, row
