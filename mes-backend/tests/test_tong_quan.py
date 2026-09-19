"""Màn Tổng quan gom vào MỘT lời gọi — con số và cảnh báo phải khớp nguồn gốc.

Trước đây màn này gọi ba endpoint rồi tự tính ở frontend. Gom xuống backend thì
được gói tin nhỏ hơn hai chục lần, nhưng đổi lại phép tính rời khỏi tầm mắt: sai
ở đây không màn nào khác đỏ, chỉ là người điều độ đọc một con số không đúng.

Nên test bám vào QUAN HỆ với nguồn, không bám con số cứng: `rework` phải bằng số
dòng vòng-2-trở-lên trong hàng đợi Kho xuất, `lines_busy` phải bằng số chuyền thật
sự đang bận — chứ không phải "phải bằng 3".
"""

from __future__ import annotations

from app.modules.board import service as board_service


def _ov(db) -> dict:
    return board_service.overview(db)


def test_xuong_trong_thi_moi_so_deu_khong(db):
    ov = _ov(db)
    assert ov["running_rounds"] == 0
    assert ov["lines_busy"] == 0
    assert ov["lines_held"] == 0
    assert ov["rework"] == 0
    assert ov["alerts"] == []
    assert ov["alerts_total"] == 0
    # 14 chuyền là dữ liệu hệ thống của migration 0002 — có sẵn kể cả khi chưa có lệnh.
    assert ov["lines_total"] == 14


def test_chuyen_dang_chay_vao_lines_busy(db, make_mo, flow):
    code = make_mo()
    flow.accept(code, 0)
    flow.handover(code)
    flow.accept(code, 1)
    flow.accept(code, 2)
    flow.qc(code, "PASS")
    flow.accept(code, 3)
    flow.accept(code, 4)
    flow.run_line(code, "L01")
    flow.run_line(code, "L02")

    ov = _ov(db)
    assert ov["running_rounds"] == 1
    assert ov["lines_busy"] == 2
    assert ov["lines_held"] == 0


def test_chuyen_dung_sinh_canh_bao_HOLD_kem_ly_do(db, make_mo, flow):
    code = make_mo()
    flow.accept(code, 0)
    flow.handover(code)
    flow.accept(code, 1)
    flow.accept(code, 2)
    flow.qc(code, "PASS")
    flow.accept(code, 3)
    flow.accept(code, 4)
    flow.run_line(code, "L01")
    flow.hold_line(code, "L01", reason="Mất điện")

    ov = _ov(db)
    assert ov["lines_held"] == 1

    hold = [a for a in ov["alerts"] if a["kind"] == "HOLD"]
    assert len(hold) == 1
    assert hold[0]["code"] == code
    assert hold[0]["lines"] == ["L01"]
    # Lý do phải đi kèm: thiếu nó thì màn hình hiện "đang dừng — undefined".
    assert hold[0]["reason"] == "Mất điện"


def test_QC_khong_dat_dem_vao_rework_va_khop_hang_doi(db, make_mo, flow):
    code = make_mo()
    flow.accept(code, 0)
    flow.handover(code)
    flow.accept(code, 1)
    flow.accept(code, 2)
    flow.qc(code, "FAIL", reason="Canh máy sai")

    ov = _ov(db)
    kho = board_service.queue(db, 0, limit=100)["items"]
    assert ov["rework"] == len([q for q in kho if q["round_no"] > 1])
    assert ov["rework"] == 1

    rework = [a for a in ov["alerts"] if a["kind"] == "REWORK"]
    assert len(rework) == 1
    assert rework[0]["code"] == code
    assert rework[0]["round_no"] == 2


def test_vong_2_dang_chay_sinh_canh_bao_RE_ROUND(db, make_mo, flow):
    """Lệnh làm bù phải mang theo con số để màn hình ghi "còn X/Y pcs"."""
    code = make_mo(qty=10_000)
    flow.accept(code, 0)
    flow.handover(code)
    flow.accept(code, 1)
    flow.accept(code, 2)
    flow.qc(code, "FAIL", reason="Canh máy sai")
    flow.accept(code, 0)
    flow.handover(code)
    flow.accept(code, 1)
    flow.accept(code, 2)
    flow.qc(code, "PASS")
    flow.accept(code, 3)
    flow.accept(code, 4)
    flow.run_line(code, "L01")

    ov = _ov(db)
    assert ov["re_round"] == 1

    re_round = [a for a in ov["alerts"] if a["kind"] == "RE_ROUND"]
    assert len(re_round) == 1
    assert re_round[0]["code"] == code
    assert re_round[0]["round_no"] == 2
    assert re_round[0]["quantity"] == 10_000
    assert re_round[0]["target_qty"] is not None


def test_alerts_total_dem_ca_phan_chua_tra_ve(db, make_mo, flow):
    """`alerts` có trần, `alerts_total` thì không — màn hình cần biết còn bao nhiêu.

    Một lệnh QC trả về sinh HAI cảnh báo, không phải một: nó vừa nằm ở hàng đợi Kho
    xuất chờ nhận lại (REWORK), vừa là một vòng 2 đang mở (RE_ROUND). Đây là hành vi
    của bản cũ, giữ nguyên — gộp lại là một thay đổi nghiệp vụ, không phải tối ưu.
    """
    for _ in range(2):
        code = make_mo()
        flow.accept(code, 0)
        flow.handover(code)
        flow.accept(code, 1)
        flow.accept(code, 2)
        flow.qc(code, "FAIL", reason="Canh máy sai")

    day_du = _ov(db)
    assert day_du["alerts_total"] == 4
    assert len(day_du["alerts"]) == 4

    cat_bot = board_service.overview(db, alert_limit=3)
    assert len(cat_bot["alerts"]) == 3
    assert cat_bot["alerts_total"] == 4
