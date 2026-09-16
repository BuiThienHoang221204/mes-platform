"""Đếm THÙNG và ba số mỗi khung giờ — BRD §7.2b + §7b.2.

Hai luật quyết định, và cả hai đều dễ bị hiểu sai nên phải có bài kiểm giữ:

1. **PCS là đơn vị gốc, thùng chỉ là cách đếm.** Tiến độ MO không bao giờ tính bằng
   thùng — mọi ràng buộc sẵn có chạy bằng pcs, mà đơn hàng hiếm khi chia hết cho
   quy cách.
2. **Thùng cuối của đơn được đóng thiếu.** `3.000 ÷ 800 = 3 thùng đầy + 1 thùng lẻ
   600`. Không có luật này thì đơn nào không chia hết cũng kẹt vĩnh viễn.

Hệ quả quan trọng nhất: **hàng lẻ KHÔNG phải hàng thiếu.** Thiếu là chưa làm ra
được → phải làm thêm → mở vòng mới. Lẻ là đã làm ra rồi, chỉ chưa gom đủ một thùng
→ không phải làm gì cả.
"""

from __future__ import annotations

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, ProgrammingError

from app.common.errors import DomainError, translate_db_error
from app.common.vocab.error_codes import Err
from app.modules.mo import repository as mo_repo
from app.modules.packing import repository as packing_repo
from app.modules.production import repository as production_repo

# `mo/models.py` khai quan hệ `rounds` bằng TÊN CHUỖI "MoRound", nên lớp đó phải được
# nạp xong trước truy vấn ORM đầu tiên. Chạy cả bộ thì file test khác nạp hộ; chạy
# riêng file này thì không ai nạp, và SQLAlchemy ném "failed to locate a name".
from app.modules.round import models as _nap_mo_round  # noqa: F401


def _toi_chuyen(flow, code: str) -> None:
    """Đưa MO xuống tới trạm 4 và cho một chuyền chạy."""
    flow.accept(code, 0)
    flow.handover(code)
    flow.accept(code, 1)
    flow.accept(code, 2)
    flow.qc(code, "PASS")
    flow.accept(code, 3)
    flow.accept(code, 4)
    flow.run_line(code, "L01")


# ══ Quy cách — cầu nối giữa hai đơn vị ══════════════════════════════════════
def test_quy_cach_luu_va_khoa_cung_sau_submit(db, make_mo):
    code = make_mo(qty=3_000, box=800)
    mo = mo_repo.get_mo(db, code)
    assert mo.pcs_per_box == 800

    # §4A: sau Submit thì quy cách khoá cứng y như `quantity`. Đổi được thì mọi dòng
    # thùng đã ghi quy ra một số pcs khác, và sản lượng vòng trước tự đổi theo.
    mo.pcs_per_box = 500
    with pytest.raises(Exception) as e:
        db.flush()
    assert "đã Submit" in str(e.value)
    db.rollback()


def test_khong_khai_quy_cach_thi_khong_dem_thung_duoc(db, make_mo, flow):
    code = make_mo(qty=3_000)          # box mặc định 0 = mặt hàng không đóng thùng
    _toi_chuyen(flow, code)
    flow.hourly(code, 8, 800)
    flow.pack_start(code)

    with pytest.raises(DomainError) as e:
        flow.pack_hourly(code, 8, 1)
    assert e.value.code == Err.NO_PCS_PER_BOX


# ══ Ba số mỗi khung giờ ═════════════════════════════════════════════════════
def test_ba_so_moi_khung_gio_xuong_toi_CSDL(db, make_mo, flow):
    code = make_mo(qty=3_000, box=800)
    _toi_chuyen(flow, code)
    flow.hourly(code, 8, qty=520, people=12, target=600)
    db.flush()

    row = db.execute(text(
        "SELECT headcount, target_qty, qty FROM hourly_output ORDER BY recorded_at DESC LIMIT 1"
    )).one()
    assert tuple(row) == (12, 600, 520)


def test_vuot_san_luong_yeu_cau_cua_MOT_khung_thi_KHONG_chan(db, make_mo, flow):
    """`Đạt 117%` là tin tốt. Chỉ mục tiêu cả VÒNG mới là trần cứng (§7.2b)."""
    code = make_mo(qty=3_000, box=800)
    _toi_chuyen(flow, code)
    flow.hourly(code, 8, qty=700, people=10, target=600)   # vượt yêu cầu khung
    db.flush()
    assert sum(h.qty for h in production_repo.hourly_of(db, flow.round_of(code).id)) == 700


def test_thieu_so_nguoi_hoac_san_luong_yeu_cau_thi_chan(db, make_mo, flow):
    code = make_mo(qty=3_000, box=800)
    _toi_chuyen(flow, code)

    with pytest.raises(DomainError) as thieu_nguoi:
        flow.hourly(code, 8, qty=500, people=0, target=600)
    with pytest.raises(DomainError) as thieu_dinh_muc:
        flow.hourly(code, 9, qty=500, people=10, target=0)
    assert thieu_nguoi.value.code == Err.HOURLY_PEOPLE
    assert thieu_dinh_muc.value.code == Err.HOURLY_TARGET


# ══ Đếm thùng — kịch bản thật của xưởng ═════════════════════════════════════
def test_hang_le_khong_bien_mat_va_khong_phai_hang_thieu(db, make_mo, flow):
    """Đơn 3.000 pcs · 800 pcs/thùng — đúng ca người dùng nêu.

    Giờ 2 làm ra 1.000 mà chỉ đóng được 1 thùng: 200 cái lẻ nằm trên bàn. Con số đó
    phải HIỆN RA, và phải tự tan vào giờ sau khi gom đủ.
    """
    code = make_mo(qty=3_000, box=800)
    _toi_chuyen(flow, code)
    flow.pack_start(code)

    flow.hourly(code, 8, 800)
    t1 = flow.pack_hourly(code, 8, boxes=1)
    assert (t1.made_pcs, t1.packed_pcs, t1.le_pcs) == (800, 800, 0)

    flow.hourly(code, 9, 1_000)
    t2 = flow.pack_hourly(code, 9, boxes=1)
    assert (t2.made_pcs, t2.packed_pcs, t2.le_pcs) == (1_800, 1_600, 200), "200 lẻ phải hiện ra"

    flow.hourly(code, 10, 1_200)
    t3 = flow.pack_hourly(code, 10, boxes=1)
    assert (t3.made_pcs, t3.packed_pcs, t3.le_pcs) == (3_000, 2_400, 600)


def test_thung_cuoi_duoc_dong_thieu_nen_don_xong_trong_MOT_vong(db, make_mo, flow):
    """Luật quyết định: `3.000 ÷ 800 = 3 thùng đầy + 1 thùng lẻ 600`.

    Không có nó thì đóng được 2.400, Nhập kho thấy `2.400 < 3.000` nên trả về Bàn
    team leader; vòng sau vẫn 600 đó, vẫn 0 thùng nguyên, lặp mãi.
    """
    code = make_mo(qty=3_000, box=800)
    _toi_chuyen(flow, code)
    flow.pack_start(code)
    flow.hourly(code, 8, 3_000)
    flow.pack_hourly(code, 8, boxes=3)              # 3 thùng đầy = 2.400, lẻ 600

    flow.close_production(code, ok=3_000)
    flow.pack(code, 3_000)                          # chốt bằng PCS, gồm cả thùng lẻ
    flow.accept(code, 5)
    out = flow.warehouse_in(code)

    assert out.outcome == "COMPLETED", "thùng cuối đóng thiếu nên đơn xong ngay vòng 1"
    assert out.qty_done == 3_000
    assert out.qty_remain == 0
    assert out.new_round_no is None, "không mở vòng hai — 600 lẻ đã vào thùng lẻ"


def test_khong_dong_duoc_nhieu_hon_so_da_lam_ra(db, make_mo, flow):
    """Hai sổ độc lập gặp nhau ở đây — trigger `packing_hourly_within_made`."""
    code = make_mo(qty=3_000, box=800)
    _toi_chuyen(flow, code)
    flow.pack_start(code)
    flow.hourly(code, 8, 800)

    # Trigger dùng `RAISE EXCEPTION` nên psycopg trả ProgrammingError, KHÔNG phải
    # IntegrityError — ràng buộc UNIQUE mới ném IntegrityError. `translate_db_error`
    # nhận cả hai, xem `errors.py`.
    with pytest.raises(ProgrammingError) as e:
        flow.pack_hourly(code, 9, boxes=3)          # 2.400 pcs > 800 đã làm ra
    loi = translate_db_error(e.value)
    assert loi is not None and loi.code == Err.BOX_OVER_MADE
    assert loi.status == 409


def test_trung_khung_gio_thi_chan(db, make_mo, flow):
    code = make_mo(qty=3_000, box=800)
    _toi_chuyen(flow, code)
    flow.pack_start(code)
    flow.hourly(code, 8, 3_000)
    flow.pack_hourly(code, 8, boxes=1)

    with pytest.raises(IntegrityError) as e:
        flow.pack_hourly(code, 8, boxes=1)
    loi = translate_db_error(e.value)
    assert loi is not None and loi.code == Err.BOX_DUP


def test_quy_cach_DONG_DAU_vao_tung_dong(db, make_mo, flow):
    """Sửa quy cách của MO không được làm sai các dòng thùng đã ghi.

    Cùng lý lẽ với `mo_round.target_qty`: tính lại thì báo cáo tháng trước tự đổi.
    """
    code = make_mo(qty=3_000, box=800)
    _toi_chuyen(flow, code)
    flow.pack_start(code)
    flow.hourly(code, 8, 1_600)
    flow.pack_hourly(code, 8, boxes=2)

    dong = packing_repo.packing_hourly_of(db, flow.round_of(code).id)
    assert [d.pcs_per_box for d in dong] == [800], "quy cách phải nằm TRÊN dòng"
    assert packing_repo.packed_boxes_pcs(db, flow.round_of(code).id) == 1_600


# ══ Truy vết phải chở đủ dữ liệu cho màn Sản xuất ═══════════════════════════
def test_trace_tra_du_ba_so_gio_va_so_thung(db, make_mo, flow):
    """`/mos/{code}/trace` là nguồn DUY NHẤT của màn trạm 4.

    Thiếu một trường ở đây thì FE không có chỗ nào khác để lấy — và nó mất lặng
    lẽ, vì endpoint này cố ý không gắn `response_model`.
    """
    from app.modules.board import service as board_service

    code = make_mo(qty=3_000, box=800)
    _toi_chuyen(flow, code)
    flow.pack_start(code)
    flow.hourly(code, 8, qty=1_000, people=12, target=800)
    flow.pack_hourly(code, 8, boxes=1)

    tr = board_service.trace(db, code)
    assert tr["pcs_per_box"] == 800, "màn Sản xuất cần quy cách trước khi ghi thùng đầu tiên"
    vong = tr["rounds"][-1]

    gio = vong["hourly"][0]
    assert (gio["headcount"], gio["target_qty"], gio["qty"]) == (12, 800, 1_000)

    thung = vong["packing_hourly"][0]
    assert (thung["boxes"], thung["pcs_per_box"]) == (1, 800)

    # 1.000 làm ra − 800 đã đóng = 200 lẻ. KHÔNG phải hàng thiếu.
    assert vong["box_summary"] == {
        "boxes_total": 1, "packed_pcs": 800, "made_pcs": 1_000, "le_pcs": 200,
    }
