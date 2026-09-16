"""Đọc mã quét — sáu tình huống của BRD §1b.2, không cần CSDL.

Đây là chỗ dễ tưởng đơn giản nhất mà sai thì hỏng nặng nhất.
"""

import pytest

from app.modules.scan.mocode import read_mo_code


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("XM068820", "M068820"),          # tiền tố 1 ký tự — trường hợp thật
        ("]Q1M076730", "M076730"),        # tiền tố 3 ký tự
        ("xm068820\r\n", "M068820"),      # chữ thường + ký tự điều khiển
        ("XMO68820", "M068820"),          # gõ chữ O thay số 0
        ("XMI68820", "M168820"),          # gõ chữ I thay số 1
        ("M068820", "M068820"),           # không tiền tố
    ],
)
def test_doc_duoc(raw: str, expected: str):
    assert read_mo_code(raw).code == expected


def test_tu_choi_bay_chu_so():
    """KHÔNG cắt bừa thành mã 6 số CÓ THẬT — loại lỗi không ai phát hiện được."""
    r = read_mo_code("XM0688201")
    assert r.code is None
    assert "Không đọc được" in (r.error or "")


def test_tu_choi_nhieu_ma():
    r = read_mo_code("XM068820M076730")
    assert r.code is None
    assert "nhiều mã" in (r.error or "")


def test_chuoi_rong():
    assert read_mo_code("   ").code is None
