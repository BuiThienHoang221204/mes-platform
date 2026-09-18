"""Chốt sổ SX không được đóng bước 4 — nếu đóng thì vòng kẹt, không đường ra.

Trạm 4 có HAI nhánh chạy song song (§7b): chuyền và đóng thùng. Chốt sổ SX mới
xong nhánh chuyền. Nhánh đóng thùng bắt buộc kết thúc SAU khi chốt sổ.

Đóng bước 4 ngay lúc chốt sổ thì lệnh rơi khỏi `at_station_rows(4)` — màn hình
Sản xuất không còn liệt kê nó, không mở được màn Kết thúc đóng thùng,
`packing.completed_at` mãi NULL, và hàng đợi Kho nhập đòi đúng cột đó nên trống
vĩnh viễn.
"""

from __future__ import annotations

from app.modules.board import repository as board_repo


def _toi_san_xuat(flow, code: str) -> None:
    flow.accept(code, 0)
    flow.handover(code)
    flow.accept(code, 1)
    flow.accept(code, 2)
    flow.qc(code, "PASS")
    flow.accept(code, 3)
    flow.accept(code, 4)


def test_chot_so_xong_van_con_o_tram_4(db, make_mo, flow):
    code = make_mo(qty=1_000, minutes=60)
    _toi_san_xuat(flow, code)
    flow.run_line(code, "L01")
    flow.close_production(code, ok=1_000)

    con = [r["code"] for r in board_repo.at_station_rows(db, 4, limit=100)]
    assert code in con, "chốt sổ xong là biến mất khỏi trạm 4 — không ai đóng thùng nốt được"


def test_di_het_duong_toi_hang_doi_kho_nhap(db, make_mo, flow):
    code = make_mo(qty=1_000, minutes=60)
    _toi_san_xuat(flow, code)
    flow.run_line(code, "L01")
    flow.pack_start(code)
    flow.close_production(code, ok=1_000)

    assert code not in [r["code"] for r in board_repo.queue_rows(db, 5, limit=100)]
    flow.pack(code, qty=1_000)
    assert code in [r["code"] for r in board_repo.queue_rows(db, 5, limit=100)]


def test_kho_nhap_quet_nhan_thi_buoc_4_moi_dong(db, make_mo, flow):
    code = make_mo(qty=1_000, minutes=60)
    _toi_san_xuat(flow, code)
    flow.run_line(code, "L01")
    flow.pack_start(code)
    flow.close_production(code, ok=1_000)
    flow.pack(code, qty=1_000)
    flow.accept(code, 5)

    assert code not in [r["code"] for r in board_repo.at_station_rows(db, 4, limit=100)]
    assert code in [r["code"] for r in board_repo.at_station_rows(db, 5, limit=100)]
