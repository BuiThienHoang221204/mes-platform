"""Kiểm thử màn Tổng quan — `board_service.overview`."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.modules.board import service as board_service
from app.modules.round import service as round_service
from app.common.vocab.enums import RETURN_TO_KHO


def _ov(db: Session, **kw) -> dict:
    return board_service.overview(db, **kw)


def test_tong_quan_khi_chua_co_lenh(db):
    """Xưởng trống: mọi con số = 0, danh sách cảnh báo rỗng."""
    ov = _ov(db)
    assert ov["running_rounds"] == 0
    assert ov["lines_busy"] == 0
    assert ov["lines_held"] == 0
    assert ov["re_round"] == 0
    assert ov["rework"] == 0
    assert ov["alerts"] == []
    assert ov["alerts_total"] == 0
    assert ov["lines_total"] == 14


def test_chuyen_dang_chay_vao_lines_busy(db, make_mo, flow):
    code = make_mo()
    flow.accept(code, 0)
    flow.handover(code)
    flow.accept(code, 1)
    flow.accept(code, 2)
    flow.accept(code, 3)
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
    flow.accept(code, 3)
    flow.run_line(code, "L01")
    flow.hold_line(code, "L01", reason="Mất điện")

    ov = _ov(db)
    assert ov["lines_held"] == 1

    hold = [a for a in ov["alerts"] if a["kind"] == "HOLD"]
    assert len(hold) == 1
    assert hold[0]["code"] == code
    assert hold[0]["lines"] == ["L01"]
    assert hold[0]["reason"] == "Mất điện"


def test_rework_dem_vao_rework_va_khop_hang_doi(db, make_mo, flow, actor):
    code = make_mo()
    flow.accept(code, 0)
    flow.handover(code)
    flow.accept(code, 1)
    mo, rnd = round_service.lock_round(db, code)
    round_service.open_next_round(
        db, mo=mo, current=rnd, returned_to_step=RETURN_TO_KHO,
        reason="Làm lại từ gốc", actor_id=actor,
    )

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
    flow.accept(code, 3)
    flow.run_line(code, "L01")
    flow.close_production(code, ok=6_000, short=4_000, short_reason="hết ca")
    flow.pack(code, 6_000)
    flow.accept(code, 4)
    flow.warehouse_in(code)

    # Vòng 2 vào Bàn team leader rồi sang Sản xuất
    flow.accept(code, 3)
    flow.run_line(code, "L01")

    ov = _ov(db)
    assert ov["re_round"] == 1

    re_round = [a for a in ov["alerts"] if a["kind"] == "RE_ROUND"]
    assert len(re_round) == 1
    assert re_round[0]["code"] == code
    assert re_round[0]["round_no"] == 2
    assert re_round[0]["quantity"] == 10_000
    assert re_round[0]["target_qty"] is not None


def test_alerts_total_dem_ca_phan_chua_tra_ve(db, make_mo, flow, actor):
    for _ in range(2):
        code = make_mo()
        flow.accept(code, 0)
        flow.handover(code)
        flow.accept(code, 1)
        mo, rnd = round_service.lock_round(db, code)
        round_service.open_next_round(
            db, mo=mo, current=rnd, returned_to_step=RETURN_TO_KHO,
            reason="Làm lại từ đầu", actor_id=actor,
        )

    day_du = _ov(db)
    assert day_du["alerts_total"] == 4
    assert len(day_du["alerts"]) == 4

    cat_bot = board_service.overview(db, alert_limit=3)
    assert len(cat_bot["alerts"]) == 3
    assert cat_bot["alerts_total"] == 4
