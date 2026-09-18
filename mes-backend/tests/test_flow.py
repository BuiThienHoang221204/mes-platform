"""Kịch bản thật của xưởng — dịch từ 116 assertion của demo.

Đây là bản đặc tả chính xác nhất đang có: nó đã từng bắt được năm lớp lỗi thật
(số âm, vòng lặp vô hạn, đếm hai lần lô cuối, bước 5 của vòng cũ khoá hàng đợi
Nhập kho, cột "Bắt đầu từ" đoán nhầm sau QC FAIL).
"""

from __future__ import annotations

import pytest
from sqlalchemy.exc import SQLAlchemyError

from app.common.errors import DomainError
from app.common.vocab.enums import RETURN_TO_BANCHO, RETURN_TO_KHO
from app.modules.mo import repository as mo_repo
from app.modules.packing import repository as packing_repo
from app.modules.qc import repository as qc_repo
from app.modules.round import repository as round_repo


# ══ Vòng lặp 9.000 + 1.000 ══════════════════════════════════════════════════
def test_vong_lap_9000_roi_1000(db, make_mo, flow):
    code = make_mo(qty=10_000, minutes=180)

    # ── Vòng 1 ──
    flow.accept(code, 0)
    flow.handover(code)
    flow.accept(code, 1)
    flow.accept(code, 2)
    flow.qc(code, "PASS")
    flow.accept(code, 3)
    flow.accept(code, 4)
    flow.run_line(code, "L01")
    flow.close_production(code, ok=9_000, ng=0, short=1_000, short_reason="Chờ bù liệu")
    flow.pack(code, 9_000, "Đóng thiếu")
    flow.accept(code, 5)
    out = flow.warehouse_in(code)

    assert out.outcome == "ROUND_OPENED", "mới đóng 9.000 thì chưa COMPLETED"
    assert out.qty_done == 9_000
    assert out.qty_remain == 1_000
    assert out.new_round_no == 2

    # ── Vòng 2 bắt đầu ở BÀN TEAM LEADER, không qua Kho/Setup/QC ──
    rnd2 = flow.round_of(code)
    assert rnd2.round_no == 2
    assert rnd2.returned_to_step == RETURN_TO_BANCHO
    assert rnd2.target_qty == 1_000, "mục tiêu vòng 2 chỉ còn phần thiếu"
    assert rnd2.required_sec == 180 * 60 * 1_000 // 10_000, "hạn mức chia theo SL của vòng"
    assert round_repo.get_step(db, rnd2.id, 3) is not None, "bước Bàn team leader mở sẵn"
    assert round_repo.get_step(db, rnd2.id, 1) is None, "không phải setup lại"
    assert qc_repo.get_qc(db, rnd2.id) is None, "kết quả QC vòng cũ không dính sang"
    assert packing_repo.get_packing(db, rnd2.id) is None, "SL đóng thùng vòng cũ không dính sang"

    # ── Vòng 2 đóng nốt 1.000 ──
    flow.accept(code, 4)
    flow.run_line(code, "L02")
    flow.close_production(code, ok=1_000)
    flow.pack(code, 1_000)
    flow.accept(code, 5)
    out2 = flow.warehouse_in(code)

    assert out2.outcome == "COMPLETED"
    assert out2.qty_done == 10_000
    assert out2.qty_remain == 0
    assert mo_repo.get_mo(db, code).status == "COMPLETED"


def test_khong_bao_gio_ra_so_am(db, make_mo, flow):
    """Lỗi cũ: so với quantity thay vì mục tiêu vòng → qtyDone vượt quantity."""
    code = make_mo(qty=10_000)
    _chay_het_vong(flow, code, ok=9_000, short=1_000, short_reason="hết ca")
    flow.warehouse_in(code)
    p = flow.progress(code)
    assert p.qty_remain >= 0
    assert p.qty_done <= p.quantity


def test_vong_moi_vao_duoc_hang_doi_nhap_kho(db, make_mo, flow):
    """Lỗi cũ: bước 5 của vòng cũ khiến MO không bao giờ vào lại hàng đợi Nhập kho."""
    code = make_mo(qty=1_000)
    _chay_het_vong(flow, code, ok=600, short=400, short_reason="hết liệu")
    flow.warehouse_in(code)

    rnd2 = flow.round_of(code)
    assert round_repo.get_step(db, rnd2.id, 5) is None, "vòng mới phải trắng bước Nhập kho"
    flow.accept(code, 4)
    flow.run_line(code, "L03")
    flow.close_production(code, ok=400)
    flow.pack(code, 400)
    flow.accept(code, 5)          # nếu bước 5 còn sót của vòng cũ thì chỗ này nổ
    assert flow.warehouse_in(code).outcome == "COMPLETED"


# ══ QC FAIL → về KHO, không về Bàn team leader ══════════════════════════════════════
def test_qc_fail_tra_ve_kho(db, make_mo, flow):
    code = make_mo(qty=10_000)
    flow.accept(code, 0)
    flow.handover(code)
    flow.accept(code, 1)
    flow.accept(code, 2)
    out = flow.qc(code, "FAIL", "Sai thông số setup")

    assert out.new_round_no == 2
    rnd2 = flow.round_of(code)
    assert rnd2.returned_to_step == RETURN_TO_KHO, "setup sai thì phải làm lại từ gốc"
    assert round_repo.get_step(db, rnd2.id, 3) is None, "KHÔNG mở sẵn bước Bàn team leader"
    assert rnd2.target_qty == 10_000, "chưa làm được cái nào nên mục tiêu giữ nguyên"

    # phải đi lại từ Kho
    with pytest.raises(DomainError):
        flow.accept(code, 1)      # chưa bàn giao lại
    flow.accept(code, 0)
    flow.handover(code)
    flow.accept(code, 1)


def test_qc_fail_khong_ghi_ly_do_bi_chan(db, make_mo, flow):
    code = make_mo()
    flow.accept(code, 0)
    flow.handover(code)
    flow.accept(code, 1)
    flow.accept(code, 2)
    with pytest.raises(SQLAlchemyError):
        flow.qc(code, "FAIL", None)


# ══ Không nhảy bước ═════════════════════════════════════════════════════════
def test_chua_ban_giao_thi_setup_khong_nhan_duoc(db, make_mo, flow):
    code = make_mo()
    flow.accept(code, 0)
    with pytest.raises(DomainError) as e:
        flow.accept(code, 1)
    assert e.value.code == "NO_HANDOVER"


def test_khong_nhay_tu_kho_thang_sang_san_xuat(db, make_mo, flow):
    code = make_mo()
    flow.accept(code, 0)
    flow.handover(code)
    with pytest.raises(DomainError) as e:
        flow.accept(code, 4)
    assert e.value.code == "SKIP_STEP"


def test_nhan_hai_lan_o_cung_tram_bi_chan(db, make_mo, flow):
    code = make_mo()
    flow.accept(code, 0)
    with pytest.raises(DomainError) as e:
        flow.accept(code, 0)
    assert e.value.code == "STEP_DONE"


# ══ Bước N đóng khi bước N+1 nhận ═══════════════════════════════════════════
def test_ai_dong_buoc_truoc_duoc_ghi_lai(db, make_mo, flow, actor):
    """Cột đáng giá nhất để truy cứu: Setup không tự bấm xong, QC nhận thì Setup mới đóng."""
    code = make_mo()
    flow.accept(code, 0)
    flow.handover(code)
    flow.accept(code, 1)
    rnd = flow.round_of(code)
    assert round_repo.get_step(db, rnd.id, 1).closed_at is None

    flow.accept(code, 2)
    step1 = round_repo.get_step(db, rnd.id, 1)
    assert step1.closed_at is not None
    assert step1.closed_by == actor, "người đóng Setup chính là người của QC"


# ══ Đóng thùng ════════════════════════════════════════════════════════════════
def test_dong_goi_vuot_sl_dat_bi_chan(db, make_mo, flow):
    code = make_mo(qty=1_000)
    _chay_toi_chot_so(flow, code, ok=800, short=200, short_reason="hết ca")
    with pytest.raises(SQLAlchemyError):
        flow.pack(code, 900)


def test_chua_chot_so_sx_thi_khong_ket_thuc_dong_goi_duoc(db, make_mo, flow):
    code = make_mo(qty=1_000)
    flow.accept(code, 0)
    flow.handover(code)
    flow.accept(code, 1)
    flow.accept(code, 2)
    flow.qc(code, "PASS")
    flow.accept(code, 3)
    flow.accept(code, 4)
    flow.run_line(code, "L04")
    with pytest.raises(SQLAlchemyError):
        flow.pack(code, 100)


# ══ Cộng dồn thời gian qua mọi vòng ═════════════════════════════════════════
def test_timer_cong_don_qua_moi_vong(db, make_mo, flow):
    """Lỗi cũ: bảng chỉ đọc vòng hiện tại nên MO qua Setup hai lần vẫn hiện "—"."""
    from sqlalchemy import text

    code = make_mo(qty=10_000)
    flow.accept(code, 0)
    flow.handover(code)
    flow.accept(code, 1)
    flow.accept(code, 2)
    flow.qc(code, "FAIL", "Sai thông số setup")      # vòng 2 về Kho
    flow.accept(code, 0)
    flow.handover(code)
    flow.accept(code, 1)
    flow.accept(code, 2)

    mo_id = mo_repo.get_mo(db, code).id
    row = db.execute(
        text("SELECT rounds FROM v_step_total WHERE mo_id = :m AND step_no = 1"), {"m": mo_id}
    ).one()
    assert row.rounds == 2, "Setup đã đi qua hai vòng — không được chỉ đếm vòng cuối"


# ══ Tiện ích ════════════════════════════════════════════════════════════════
def _chay_toi_chot_so(flow, code: str, *, ok: int, ng: int = 0, short: int = 0,
                      ng_reason=None, short_reason=None):
    flow.accept(code, 0)
    flow.handover(code)
    flow.accept(code, 1)
    flow.accept(code, 2)
    flow.qc(code, "PASS")
    flow.accept(code, 3)
    flow.accept(code, 4)
    flow.run_line(code, "L05")
    flow.close_production(code, ok=ok, ng=ng, short=short,
                          ng_reason=ng_reason, short_reason=short_reason)


def _chay_het_vong(flow, code: str, *, ok: int, ng: int = 0, short: int = 0,
                   ng_reason=None, short_reason=None):
    _chay_toi_chot_so(flow, code, ok=ok, ng=ng, short=short,
                      ng_reason=ng_reason, short_reason=short_reason)
    flow.pack(code, ok)
    flow.accept(code, 5)


# ══ Danh sách lệnh — màn Kế hoạch không có đường nào khác ═══════════════════
def test_liet_ke_lenh_loc_theo_trang_thai(db, actor, make_mo):
    """Lệnh vừa tạo ở DRAFT KHÔNG nằm trong hàng đợi trạm nào.

    Không có `GET /mos` thì màn Kế hoạch tạo xong là mất dấu — chỉ tìm lại được
    nếu người dùng nhớ mã.
    """
    from app.common.vocab.enums import MoStatus
    from app.modules.mo import service as mo_service

    make_mo()                                    # tạo + submit → PROCESSING
    mo_service.create(db, [mo_service.NewMo("M800001", "Vỏ nhựa F3", 500, 3600, 800)], actor)
    db.flush()

    nhap = {m.code for m in mo_repo.list_mos(db, status=MoStatus.DRAFT, limit=50)}
    assert "M800001" in nhap, "lệnh DRAFT phải tìm lại được"

    tat_ca = mo_repo.list_mos(db, limit=50)
    assert len(tat_ca) >= 2
    assert tat_ca[0].created_at >= tat_ca[-1].created_at, "mới nhất phải đứng trước"
