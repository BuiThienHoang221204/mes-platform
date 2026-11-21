"""Kiểm thử tầng đọc của bảng điều hành — `board/`."""

from __future__ import annotations

import pytest
from sqlalchemy.orm import Session

from app.modules.board import repository as board_repo
from app.modules.board import service as board_service


def _queue(db: Session, station: int) -> list[dict]:
    return board_repo.queue_rows(db, station, limit=50)


def _at(db: Session, station: int) -> list[dict]:
    return board_repo.at_station_rows(db, station, limit=50)


def test_queue_va_counts_khong_bao_gio_lech_nhau(db, make_mo, flow):
    """Quy tắc vàng của bảng điều hành: số trên badge PHẢI bằng đúng số dòng.

    Nếu một ngày nào đó ai viết lại `queue_counts` bằng câu SQL riêng thay vì dùng
    chung `QUEUE_SQL`, test này sẽ bắt quả tang ngay khi có điều kiện lọc mới lọt
    vào một trong hai câu mà câu kia không có.
    """
    for _ in range(2):
        code = make_mo()
        flow.accept(code, 0)
        flow.handover(code)

    cho, _ = board_service.station_counts(db)
    for s in (0, 1, 2, 3, 4):
        rows = _queue(db, s)
        assert cho[s] == len(rows), (
            f"trạm {s}: badge hiện {cho[s]} nhưng danh sách có {len(rows)} dòng"
        )


def test_counts_chuyen_ngay_khi_quet_nhan(db, make_mo, flow):
    """Quét nhận ở trạm 0: hàng chờ trạm 0 giảm 1, hàng chờ trạm 1 KHÔNG tăng."""
    code = make_mo()
    truoc_cho, truoc_giu = board_service.station_counts(db)
    assert truoc_cho[0] == 1 and truoc_giu[0] == 0

    flow.accept(code, 0)

    sau_cho, sau_giu = board_service.station_counts(db)
    assert sau_cho[0] == 0, "đã nhận thì không còn trong hàng chờ trạm 0"
    assert sau_giu[0] == 1, "đã nhận thì vào nhóm 'đang giữ' của trạm 0"
    assert sau_cho[1] == 0, "chưa bàn giao thì trạm 1 chưa thấy việc"


def test_counts_hien_tram_1_ngay_khi_ban_giao(db, make_mo, flow):
    """Bàn giao ở trạm 0: lệnh rơi vào hàng chờ trạm 1."""
    code = make_mo()
    flow.accept(code, 0)
    flow.handover(code)

    cho, giu = board_service.station_counts(db)
    assert cho[1] == 1, "bàn giao rồi thì trạm 1 phải thấy việc trong hàng chờ"
    assert giu[0] == 1, "trạm 0 vẫn giữ phiếu cho tới khi trạm 1 quét nhận"


def test_holding_dem_viec_dang_trong_tay_khong_dem_hang_cho(db, make_mo, flow):
    """Cột 'đang ở trạm' đọc từ `mo_step.closed_at IS NULL`, không đọc từ hàng chờ.

    Lệnh đã quét nhận thì RỜI hàng chờ. Nếu chỉ đếm hàng chờ thì ba lệnh đang lắp
    ráp ở trạm 3 hiện thành 0, và người đọc tưởng xưởng trống hoặc hệ thống hỏng.
    """
    for _ in range(3):
        code = make_mo()
        flow.accept(code, 0)
        flow.handover(code)
        flow.accept(code, 1)
        flow.accept(code, 2)
        flow.accept(code, 3)

    cho, giu = board_service.station_counts(db)
    assert all(n == 0 for n in cho.values()), "không lệnh nào còn chờ nhận"
    assert giu[3] == 3, "ba lệnh đang trong tay Sản xuất phải đếm được"
    assert sum(giu.values()) == 3


def test_tram_0_dem_rieng_hai_nhom(db, make_mo, flow):
    """Kho có hai nhóm rời nhau, và giờ chúng nằm ở hai con số khác nhau."""
    chua_nhan = make_mo()
    da_nhan = make_mo()
    flow.accept(da_nhan, 0)

    cho, giu = board_service.station_counts(db)
    assert cho[0] == 1 and chua_nhan in [r["code"] for r in _queue(db, 0)]
    assert giu[0] == 1 and da_nhan in [r["code"] for r in _at(db, 0)]


def test_at_station_la_viec_DANG_cam_khong_phai_hang_doi(db, make_mo, flow):
    """Hai danh sách phải rời nhau: nhận rồi thì rời hàng đợi, sang `at_station`."""
    mo = make_mo()
    assert mo in [r["code"] for r in _queue(db, 0)]
    assert mo not in [r["code"] for r in _at(db, 0)]

    flow.accept(mo, 0)
    assert mo not in [r["code"] for r in _queue(db, 0)]
    giu = [r for r in _at(db, 0) if r["code"] == mo]
    assert len(giu) == 1
    assert giu[0]["accepted_by"]
    assert giu[0]["holding_sec"] >= 0


def test_at_station_nha_lenh_khi_tram_sau_quet_nhan(db, make_mo, flow):
    """Bước chỉ đóng khi trạm SAU nhận — lúc đó lệnh phải rời khỏi trạm trước."""
    mo = make_mo()
    flow.accept(mo, 0)
    flow.handover(mo)
    flow.accept(mo, 1)

    assert mo not in [r["code"] for r in _at(db, 0)]
    assert mo in [r["code"] for r in _at(db, 1)]


def test_hang_doi_tram_2_hien_lenh_khi_tram_1_da_nhan(db, make_mo, flow):
    """Setup máy xong thì lệnh rơi vào hàng chờ của Bàn team leader (trạm 2)."""
    mo = make_mo()
    flow.accept(mo, 0)
    flow.handover(mo)
    flow.accept(mo, 1)

    assert mo in [r["code"] for r in _queue(db, 2)]


def test_hang_doi_luon_co_waiting_sec(db, make_mo, flow):
    """Màn trạm hiện cột `chờ bao lâu` — thiếu trường là cả cột hiện dấu gạch."""
    mo = make_mo()
    flow.accept(mo, 0)
    flow.handover(mo)
    rows = _queue(db, 1)
    assert rows and rows[0]["waiting_sec"] is not None
    assert rows[0]["waiting_sec"] >= 0


def test_trace_khong_bi_N_cong_1_khi_tang_vong(db, make_mo, flow, dem_sql):
    code = make_mo(qty=1000)
    flow.accept(code, 0)
    flow.handover(code)
    flow.accept(code, 1)
    flow.accept(code, 2)
    flow.accept(code, 3)
    flow.run_line(code, "L01")
    flow.close_production(code, ok=500, short=500, short_reason="Thiếu vật tư")
    flow.pack(code, 500)
    flow.accept(code, 4)

    db.flush()
    with dem_sql(db) as mot_vong:
        board_service.trace(db, code)

    flow.warehouse_in(code)   # mở vòng 2
    assert flow.round_of(code).round_no == 2

    db.flush()
    with dem_sql(db) as hai_vong:
        board_service.trace(db, code)

    assert len(hai_vong) == len(mot_vong), (
        f"MO một vòng tốn {len(mot_vong)} câu, hai vòng tốn {len(hai_vong)} — "
        f"truy vấn đã lọt lại vào vòng lặp"
    )


def test_trace_van_tra_du_du_lieu_cua_tung_vong(db, make_mo, flow):
    code = make_mo(qty=1000)
    flow.accept(code, 0)
    flow.handover(code)
    flow.accept(code, 1)
    flow.accept(code, 2)
    flow.accept(code, 3)
    flow.run_line(code, "L01")
    flow.close_production(code, ok=500, short=500, short_reason="Thiếu vật tư")
    flow.pack(code, 500)
    flow.accept(code, 4)
    flow.warehouse_in(code)

    cay = board_service.trace(db, code)
    assert len(cay["rounds"]) == 2

    vong1, vong2 = cay["rounds"]
    assert vong1["round_no"] == 1 and vong2["round_no"] == 2
    assert [s["step_no"] for s in vong1["steps"]] == [0, 1, 2, 3, 4]
    assert [s["step_no"] for s in vong2["steps"]] == [2]
    assert vong1["closed_at"] is not None and vong2["closed_at"] is None
