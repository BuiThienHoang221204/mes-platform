"""Chặn khởi động khi có người bật nhiều tiến trình.

`event_bus` và `read_cache` giữ trạng thái trong bộ nhớ MỘT tiến trình. Chạy nhiều
tiến trình thì cả hai sai kiểu không báo gì — xem `docs/RA-SOAT-POLLING.md` §2/A1
và §2/A2. Thà gãy lúc khởi động.
"""

from __future__ import annotations

import pytest

from app.common.config import settings
from app.common.single_process import (
    WORKER_COUNT_ENV_VARS,
    assert_single_process,
    requested_worker_count,
)


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    for name in WORKER_COUNT_ENV_VARS:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr(settings, "allow_multi_process", False)


def test_khong_khai_gi_thi_coi_nhu_mot_tien_trinh():
    assert requested_worker_count() == 1
    assert_single_process()


@pytest.mark.parametrize("name", WORKER_COUNT_ENV_VARS)
def test_moi_bien_moi_truong_deu_bi_chan(monkeypatch, name: str):
    """Ba biến, ba cách người ta hay tăng worker — bỏ sót một cái là bỏ sót cả."""
    monkeypatch.setenv(name, "4")
    assert requested_worker_count() == 4
    with pytest.raises(RuntimeError) as err:
        assert_single_process()
    assert "MỘT" in str(err.value)
    assert "RA-SOAT-POLLING" in str(err.value), "thông báo phải chỉ được chỗ đọc tiếp"


def test_mot_tien_trinh_thi_cho_qua(monkeypatch):
    monkeypatch.setenv("WEB_CONCURRENCY", "1")
    assert_single_process()


def test_mo_cong_khi_da_ra_cho_dung_chung(monkeypatch):
    """Làm xong §5.4 thì đặt MES_ALLOW_MULTI_PROCESS=true là chạy được."""
    monkeypatch.setenv("WEB_CONCURRENCY", "4")
    monkeypatch.setattr(settings, "allow_multi_process", True)
    assert_single_process()


@pytest.mark.parametrize("value", ["", "nhieu", "0", "-3", "2.5"])
def test_gia_tri_la_khong_lam_gay_khoi_dong(monkeypatch, value: str):
    """Biến môi trường gõ sai không được biến thành sự cố khởi động."""
    monkeypatch.setenv("WEB_CONCURRENCY", value)
    assert requested_worker_count() == 1
    assert_single_process()


def test_thong_bao_noi_ro_phai_lam_gi(monkeypatch):
    monkeypatch.setenv("WEB_CONCURRENCY", "4")
    with pytest.raises(RuntimeError) as err:
        assert_single_process()
    message = str(err.value)
    assert "WEB_CONCURRENCY" in message, "phải nói rõ biến nào đang gây ra"
    assert "MES_ALLOW_MULTI_PROCESS" in message, "phải nói rõ đường mở cổng"
