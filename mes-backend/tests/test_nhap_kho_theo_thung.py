"""Kho nhận đúng số đã đóng thùng — không nhận số đếm nào từ client.

Trước đây endpoint có ô `qty_received` cho kho "đếm lại". Con số ấy được ghi xuống
CSDL nhưng **không ai đọc**: §8 tính tiến độ từ `SUM(packing.qty_packed)`, nên gõ 0
hay 999.999 đều ra cùng một kết cục. Một ô nhập không đổi được gì còn tệ hơn ô nhập
sai — nó dạy người vận hành rằng số họ gõ không quan trọng.

Ba test dưới đây khoá đúng ba mệnh đề của quyết định đó.
"""

from __future__ import annotations

import pytest
from sqlalchemy import text

from app.common.errors import DomainError


def _toi_tram_4(flow, code: str) -> None:
    flow.accept(code, 0)
    flow.handover(code)
    flow.accept(code, 1)
    flow.accept(code, 2)
    flow.qc(code, "PASS")
    flow.accept(code, 3)
    flow.accept(code, 4)
    flow.run_line(code, "L01")


def _toi_kho_nhap(flow, code: str, *, target: int, ok: int) -> None:
    """Chạy trọn một vòng tới lúc Kho nhập đã quét nhận, chưa bấm Hoàn thành.

    Ba số của chốt sổ phải cộng đúng bằng mục tiêu vòng (§7.5), nên làm thiếu thì
    phần hụt phải khai lý do — trigger `production_balances` kiểm lại.
    """
    _toi_tram_4(flow, code)
    flow.hourly(code, 8, ok)
    short = target - ok
    flow.close_production(code, ok=ok, short=short,
                          short_reason="Hết ca chưa xong" if short else None)
    flow.pack(code, ok)
    flow.accept(code, 5)


def _so_da_nhan(db, code: str) -> int | None:
    return db.execute(text(
        "SELECT w.qty_received FROM warehouse_in w"
        " JOIN mo_round r ON r.id = w.round_id"
        " JOIN manufacturing_order m ON m.id = r.mo_id"
        " WHERE m.code = :c ORDER BY r.round_no DESC LIMIT 1"), {"c": code}).scalar()


def test_so_nhap_kho_LUON_bang_so_da_dong_thung(db, make_mo, flow):
    """Hàng vào thùng bao nhiêu thì kho nhận bấy nhiêu — không có đường nào khác."""
    code = make_mo(qty=3_000, box=500)
    _toi_kho_nhap(flow, code, target=3_000, ok=3_000)
    flow.warehouse_in(code)

    assert _so_da_nhan(db, code) == 3_000


def test_khong_con_cach_nao_gui_so_dem_len(db, make_mo, flow):
    """Chữ ký hàm không còn nhận `qty_received` — gửi lên là lỗi ngay lúc gọi.

    Test này canh CHỮ KÝ chứ không canh giá trị: chỗ hỏng thật sự không phải một
    con số sai, mà là việc mở lại đường cho client quyết số nhập kho.
    """
    from app.modules.warehouse_in import service as warehouse_in_service

    code = make_mo(qty=3_000, box=500)
    _toi_kho_nhap(flow, code, target=3_000, ok=3_000)

    with pytest.raises(TypeError):
        warehouse_in_service.complete(  # type: ignore[call-arg]
            db, code=code, qty_received=1, actor_id=flow.round_of(code).id)


def test_dong_thieu_thi_van_mo_vong_moi_theo_so_da_dong_thung(db, make_mo, flow):
    """Thiếu SL là chuyện của SẢN XUẤT, không phải của kho.

    Vòng 1 đóng 2.000/3.000 — kho không có cách nào khai khác đi, và §8 vẫn mở vòng
    hai đúng bằng phần còn thiếu.
    """
    code = make_mo(qty=3_000, box=500)
    _toi_kho_nhap(flow, code, target=3_000, ok=2_000)
    out = flow.warehouse_in(code)

    assert out.outcome == "ROUND_OPENED"
    assert (out.qty_done, out.qty_remain) == (2_000, 1_000)
    assert _so_da_nhan(db, code) == 2_000


def test_mat_hang_khong_dong_thung_van_nhap_duoc(db, make_mo, flow):
    """`pcs_per_box = 0` — không quy ra thùng được, nhưng vẫn phải nhập kho được."""
    code = make_mo(qty=2_000, box=0)
    _toi_kho_nhap(flow, code, target=2_000, ok=2_000)
    out = flow.warehouse_in(code)

    assert out.outcome == "COMPLETED"
    assert _so_da_nhan(db, code) == 2_000


def test_chua_ket_thuc_dong_thung_thi_KHONG_QUET_NHAN_duoc(db, make_mo, flow):
    """Không có số đã đóng thùng thì không có gì để nhận.

    Lá chắn nằm ở lúc QUÉT NHẬN chứ không phải lúc bấm Hoàn thành — kho không mở
    nổi màn hình cho một vòng chưa đóng thùng xong. `complete()` vẫn giữ kiểm tra
    trùng một lần nữa, nhưng đường thường không ai tới được đó.
    """
    code = make_mo(qty=3_000, box=500)
    _toi_tram_4(flow, code)
    flow.hourly(code, 8, 3_000)
    flow.close_production(code, ok=3_000)

    with pytest.raises(DomainError) as e:
        flow.accept(code, 5)
    assert "đóng thùng" in str(e.value)
