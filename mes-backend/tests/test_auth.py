"""Refresh token: xoay vòng, bắt dùng lại, thu hồi.

Đây là phần dễ làm sai nhất của đăng nhập. Làm thiếu xoay vòng thì refresh bị lộ
dùng được suốt cả ca; làm thiếu bắt-dùng-lại thì lộ rồi cũng không ai biết.
"""

from __future__ import annotations

import pytest
from sqlalchemy import select

from app.common.errors import Forbidden
from app.common.security.tokens import hash_pin
from app.modules.auth import repository as auth_repo
from app.modules.auth import service as auth_service
from app.modules.auth.models import AppUser, RefreshToken


@pytest.fixture
def user(db):
    """Một tài khoản thật để đăng nhập, PIN 1234."""
    u = AppUser(full_name="Thợ A", emp_code="NV999", pin_hash=hash_pin("1234"),
                roles=["PRODUCTION_LEADER"])
    db.add(u)
    db.flush()
    return u


def test_dang_nhap_tra_ca_access_lan_refresh(db, user):
    pair = auth_service.login(db, emp_code="NV999", pin="1234")
    assert pair.access_token and pair.refresh_token
    assert pair.access_token != pair.refresh_token
    assert pair.roles == ["PRODUCTION_LEADER"]


def test_sai_pin_va_sai_ma_bao_CUNG_MOT_CAU(db, user):
    """Phân biệt hai câu là nói cho người dò biết mã nhân viên nào có thật."""
    with pytest.raises(Forbidden) as sai_pin:
        auth_service.login(db, emp_code="NV999", pin="0000")
    with pytest.raises(Forbidden) as sai_ma:
        auth_service.login(db, emp_code="KHONG-CO", pin="1234")
    assert str(sai_pin.value) == str(sai_ma.value)


def test_refresh_khong_luu_chuoi_goc_vao_db(db, user):
    """Rò CSDL thì kẻ đọc được cũng không dựng lại được token."""
    pair = auth_service.login(db, emp_code="NV999", pin="1234")
    rows = db.scalars(select(RefreshToken)).all()
    assert len(rows) == 1
    assert pair.refresh_token not in rows[0].token_hash
    assert len(rows[0].token_hash) == 64  # sha256 hex


def test_lam_moi_XOAY_VONG_token_cu_chet_ngay(db, user):
    cu = auth_service.login(db, emp_code="NV999", pin="1234")
    fresh = auth_service.refresh(db, refresh_raw=cu.refresh_token)

    assert fresh.refresh_token != cu.refresh_token, "phải phát refresh MỚI"
    # KHÔNG đòi access khác nhau: payload JWT chỉ có sub/typ/exp, mà exp tính bằng
    # GIÂY — hai lần cấp trong cùng một giây cho ra chuỗi y hệt. Vô hại, vì access
    # không phải thứ để thu hồi; refresh mới là thứ phải đổi.

    # Token cũ bị đánh dấu đã dùng và trỏ sang token thay thế nó
    from app.common.security.tokens import hash_token
    row_cu = auth_repo.find_refresh(db, hash_token(cu.refresh_token))
    assert row_cu.used_at is not None
    assert row_cu.replaced_by is not None


def test_dung_lai_refresh_da_doi_thi_THU_HOI_CA_CHUOI(db, user):
    """Kịch bản token bị sao chép.

    Kẻ trộm và người thật cùng giữ một refresh. Ai đó đổi trước; người còn lại
    gửi token cũ lên. Hệ thống không biết ai là ai, nên cắt sạch mọi phiên.
    """
    cu = auth_service.login(db, emp_code="NV999", pin="1234")
    fresh = auth_service.refresh(db, refresh_raw=cu.refresh_token)

    with pytest.raises(Forbidden) as e:
        auth_service.refresh(db, refresh_raw=cu.refresh_token)
    assert "dùng lại" in str(e.value)

    # Token MỚI cũng phải chết theo — không thì kẻ trộm vẫn còn đường vào
    with pytest.raises(Forbidden):
        auth_service.refresh(db, refresh_raw=fresh.refresh_token)


def test_dang_xuat_thi_refresh_het_dung_duoc(db, user):
    pair = auth_service.login(db, emp_code="NV999", pin="1234")
    auth_service.logout(db, refresh_raw=pair.refresh_token)
    with pytest.raises(Forbidden) as e:
        auth_service.refresh(db, refresh_raw=pair.refresh_token)
    assert "thu hồi" in str(e.value)


def test_refresh_het_han_thi_khong_doi_duoc(db, user):
    from datetime import timedelta

    from app.common.clock import now

    pair = auth_service.login(db, emp_code="NV999", pin="1234")
    from app.common.security.tokens import hash_token

    row = auth_repo.find_refresh(db, hash_token(pair.refresh_token))
    # Lùi CẢ HAI mốc: CHECK refresh_expires_after_issued đòi expires_at > issued_at,
    # nên chỉ lùi mỗi expires_at là vi phạm ràng buộc chứ không phải hết hạn.
    row.issued_at = now() - timedelta(days=8)
    row.expires_at = now() - timedelta(days=1)
    db.flush()

    with pytest.raises(Forbidden) as e:
        auth_service.refresh(db, refresh_raw=pair.refresh_token)
    assert "hết hạn" in str(e.value)


def test_token_bia_dat_bi_tu_choi(db, user):
    with pytest.raises(Forbidden):
        auth_service.refresh(db, refresh_raw="toi-bia-ra-chuoi-nay")


def test_tat_tai_khoan_thi_khong_lam_moi_duoc(db, user):
    """Thu hồi quyền có hiệu lực ngay, không đợi token hết hạn."""
    pair = auth_service.login(db, emp_code="NV999", pin="1234")
    user.is_active = False
    db.flush()
    with pytest.raises(Forbidden):
        auth_service.refresh(db, refresh_raw=pair.refresh_token)
