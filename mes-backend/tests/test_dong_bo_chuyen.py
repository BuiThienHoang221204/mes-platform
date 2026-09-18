"""§7.5 [16] — các chuyền của một lệnh phải đóng ĐỒNG BỘ.

Điều kiện chặn có HAI vế, và trước bản này chỉ vế đầu được kiểm:

    1. chuyền chưa vào Đang lắp ráp lần nào   → `never_ran`, đã có
    2. chuyền đã chạy rồi ĐANG DỪNG           → lọt, vì nó có đoạn RUN trong lịch sử

Vế hai lọt là lỗi câm: chốt sổ lúc cả lệnh đứng im thì SL đạt là số của một ca
chưa làm xong, mà vòng đã đóng mất rồi — không mở lại được để làm tiếp.
"""

from __future__ import annotations

import pytest

from app.common.errors import DomainError
from app.common.vocab.error_codes import Err


def _toi_buoc_san_xuat(flow, code: str) -> None:
    flow.accept(code, 0)
    flow.handover(code)
    flow.accept(code, 1)
    flow.accept(code, 2)
    flow.qc(code, "PASS")
    flow.accept(code, 3)
    flow.accept(code, 4)


def test_chuyen_chua_chay_lan_nao_thi_chan(db, make_mo, flow):
    code = make_mo(qty=1_000, minutes=60)
    _toi_buoc_san_xuat(flow, code)
    flow.run_line(code, "L01")
    flow.assign_only(code, "L02")

    with pytest.raises(DomainError) as e:
        flow.close_production(code, ok=1_000)
    assert e.value.code == Err.LINE_NOT_RUN


def test_con_chuyen_dang_dung_thi_chan(db, make_mo, flow):
    code = make_mo(qty=1_000, minutes=60)
    _toi_buoc_san_xuat(flow, code)
    flow.run_line(code, "L01")
    flow.hold_line(code, "L01", reason="Hỏng khuôn ép")

    with pytest.raises(DomainError) as e:
        flow.close_production(code, ok=1_000)
    assert e.value.code == Err.LINE_HELD
    assert "L01" in str(e.value), "câu lỗi phải gọi đúng tên chuyền (§7.5)"


def test_tat_ca_chuyen_dung_thi_van_chan(db, make_mo, flow):
    code = make_mo(qty=1_000, minutes=60)
    _toi_buoc_san_xuat(flow, code)
    for ln in ("L01", "L02", "L03"):
        flow.run_line(code, ln)
        flow.hold_line(code, ln, reason="Mất điện toàn xưởng")

    with pytest.raises(DomainError) as e:
        flow.close_production(code, ok=1_000)
    assert e.value.code == Err.LINE_HELD
    for ln in ("L01", "L02", "L03"):
        assert ln in str(e.value)


def test_cho_chay_lai_het_thi_chot_so_duoc(db, make_mo, flow):
    code = make_mo(qty=1_000, minutes=60)
    _toi_buoc_san_xuat(flow, code)
    flow.run_line(code, "L01")
    flow.hold_line(code, "L01", reason="Hỏng khuôn ép")
    flow.start_line(code, "L01")

    row = flow.close_production(code, ok=1_000)
    assert row.qty_ok == 1_000
