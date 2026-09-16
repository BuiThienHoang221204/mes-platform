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
