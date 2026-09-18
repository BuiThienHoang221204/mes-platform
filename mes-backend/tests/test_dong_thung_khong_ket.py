"""Sổ đóng thùng chưa mở KHÔNG được thành ngõ cụt.

Sổ đóng thùng không mang quyết định nào của người dùng — nó chỉ là dòng dữ liệu để
treo `qty_packed` vào. Nhưng cả `ghi thùng theo giờ` lẫn `kết thúc đóng thùng` đều
từng từ chối khi chưa có nó.

Hậu quả: một vòng chạy suốt ca mà không ai ghi thùng giờ nào sẽ KẸT. Tới bước kết
thúc thì cả hai nút đều trả "Chưa bắt đầu đóng thùng", và không màn hình nào còn
chỗ để bắt đầu — vòng không đóng được, lệnh không sang được Kho nhập.
"""

from __future__ import annotations

import pytest

from app.common.errors import DomainError
from app.common.vocab.error_codes import Err
from app.modules.packing import repository as packing_repo


def _toi_san_xuat(flow, code: str) -> None:
    flow.accept(code, 0)
    flow.handover(code)
    flow.accept(code, 1)
    flow.accept(code, 2)
    flow.qc(code, "PASS")
    flow.accept(code, 3)
    flow.accept(code, 4)


def test_ket_thuc_duoc_du_chua_ghi_thung_gio_nao(db, make_mo, flow):
    """Đúng ca người dùng gặp: chốt sổ SX rồi, sổ thùng chưa mở lần nào."""
    code = make_mo(qty=200, minutes=60)
    _toi_san_xuat(flow, code)
    flow.run_line(code, "L01")
    flow.close_production(code, ok=200)

    rnd = flow.round_of(code)
    assert packing_repo.get_packing(db, rnd.id) is None, "phải đúng là chưa mở sổ"

    row = flow.pack(code, qty=200)
    assert row.qty_packed == 200
    assert row.started_at is not None, "sổ tự mở, không bắt bấm nút riêng"


def test_ghi_thung_dau_tien_tu_mo_so(db, make_mo, flow):
    code = make_mo(qty=1_000, minutes=60, box=200)
    _toi_san_xuat(flow, code)
    flow.run_line(code, "L01")
    flow.hourly(code, slot=8, qty=600)

    rnd = flow.round_of(code)
    assert packing_repo.get_packing(db, rnd.id) is None

    flow.pack_hourly(code, slot=8, boxes=1)
    assert packing_repo.get_packing(db, rnd.id) is not None


def test_chua_chuyen_nao_chay_thi_van_chan(db, make_mo, flow):
    """§7b không nới: phải có hàng ra khỏi chuyền mới đóng thùng được.

    Điều kiện này nói về HÀNG có tồn tại hay không — khác hẳn việc sổ đã mở chưa.
    """
    code = make_mo(qty=1_000, minutes=60)
    _toi_san_xuat(flow, code)
    flow.assign_only(code, "L01")

    with pytest.raises(DomainError) as e:
        flow.pack_start(code)
    assert e.value.code == Err.NO_RUN


def test_bam_thang_nut_bat_dau_lan_hai_van_bao_loi(db, make_mo, flow):
    """Mở NGẦM thì im lặng, nhưng bấm THẲNG nút lúc sổ đã mở thì phải báo.

    Bấm một nút mà không có gì xảy ra, lại không báo gì, thì người dùng tưởng vừa
    làm được việc.
    """
    code = make_mo(qty=1_000, minutes=60)
    _toi_san_xuat(flow, code)
    flow.run_line(code, "L01")
    flow.pack_start(code)

    with pytest.raises(DomainError) as e:
        flow.pack_start(code)
    assert e.value.code == Err.PACK_STARTED
