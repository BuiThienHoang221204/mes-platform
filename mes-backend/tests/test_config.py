"""Đơn vị thời gian có khớp tên biến không.

`access_ttl_minutes = 15` chỉ là con số 15, không mang đơn vị. Đơn vị nằm ở dòng
`timedelta(minutes=…)` trong security.py. Không gì buộc hai chỗ đó khớp nhau —
gõ nhầm `days=` thì token sống 15 NGÀY mà tên biến vẫn ghi `minutes`.

Những test này đo hạn của token THẬT rồi so lại với cấu hình, nên gõ nhầm là đỏ.
Không cần CSDL.
"""

from __future__ import annotations

import jwt

from app.common.clock import now
from app.common.config import settings
from app.common.security.tokens import make_access_token, make_refresh_token, make_station_token

NGUOI = "11111111-1111-1111-1111-111111111111"
SAI_SO = 60  # giây; chênh lệch chấp nhận được giữa lúc sinh và lúc đo


def _con_bao_nhieu_giay(token: str) -> float:
    payload = jwt.decode(token, settings.jwt.secret, algorithms=["HS256"])
    return payload["exp"] - now().timestamp()


def test_access_song_dung_so_PHUT_da_cau_hinh():
    mong_doi = settings.jwt.access_ttl_minutes * 60
    assert abs(_con_bao_nhieu_giay(make_access_token(NGUOI)) - mong_doi) < SAI_SO


def test_refresh_song_dung_so_NGAY_da_cau_hinh():
    _, _, het_han = make_refresh_token()
    mong_doi = settings.jwt.refresh_ttl_days * 86400
    assert abs((het_han - now()).total_seconds() - mong_doi) < SAI_SO


def test_station_song_dung_so_NGAY_da_cau_hinh():
    mong_doi = settings.jwt.station_ttl_days * 86400
    assert abs(_con_bao_nhieu_giay(make_station_token(0)) - mong_doi) < SAI_SO


def test_access_phai_NGAN_HON_refresh():
    """Access dài hơn refresh thì cả cơ chế refresh mất ý nghĩa."""
    assert settings.jwt.access_ttl_minutes * 60 < settings.jwt.refresh_ttl_days * 86400


def test_moi_nhom_cau_hinh_deu_co_trong_GROUPS():
    """`GROUPS` là thứ gom mọi cấu hình thiếu vào MỘT thông báo.

    Thêm nhóm vào `Settings` mà quên thêm dòng ở đây thì nhóm đó vẫn chạy — nhưng
    biến gõ sai của nó ném lỗi pydantic thô giữa lúc khởi động, thay vì nằm chung
    bảng "thiếu cái này, sai cái kia" mà người vận hành đọc được.

    Đây chính là chỗ tôi đã lọt khi thêm nhóm AUTH.
    """
    from pydantic_settings import BaseSettings

    from app.common.config import GROUPS, Settings

    trong_settings = {
        ten for ten, f in Settings.model_fields.items()
        if isinstance(f.annotation, type) and issubclass(f.annotation, BaseSettings)
    }
    da_dang_ky = {ten for ten, _, _ in GROUPS}
    assert trong_settings == da_dang_ky, (
        f"lệch — chỉ có ở Settings: {trong_settings - da_dang_ky}, "
        f"chỉ có ở GROUPS: {da_dang_ky - trong_settings}"
    )


def test_tien_to_trong_GROUPS_khop_voi_lop():
    """Tiền tố ghi sai thì thông báo lỗi chỉ người ta sửa nhầm biến môi trường."""
    from app.common.config import GROUPS

    for ten, prefix, Lop in GROUPS:
        assert Lop.model_config.get("env_prefix") == prefix, ten
