"""Màn hình điều hành: con số phải khớp danh sách, và số câu SQL không được tăng.

Hai loại lỗi ở đây đều KHÔNG làm test nào khác đỏ:

* Badge hiện một số, bấm vào ra số khác — vì câu đếm và câu liệt kê trôi khỏi nhau.
* `trace` hỏi CSDL từng vòng một — chạy vẫn đúng, chỉ là chậm dần theo số vòng.
"""

from __future__ import annotations

from contextlib import contextmanager

from sqlalchemy import event

from app.common.vocab.enums import STEP_NAMES
from app.modules.board import service as board_service


def _queue(db, station: int) -> list[dict]:
    return board_service.queue(db, station, limit=100)["items"]

def _at(db, station: int) -> list[dict]:
    return board_service.at_station(db, station, limit=100)["items"]

@contextmanager
def dem_sql(db):
    """Đếm số câu lệnh gửi xuống CSDL trong khối `with`."""
    so = []
    bind = db.get_bind()

    def nghe(conn, cursor, statement, params, context, executemany):
        so.append(statement.strip().split()[0].upper())

    event.listen(bind, "before_cursor_execute", nghe)
    try:
        yield so
    finally:
        event.remove(bind, "before_cursor_execute", nghe)

def test_badge_cho_nhan_khop_danh_sach(db, make_mo, flow):
    """`counts` và `queue` dựng từ cùng một nguồn SQL — phải ra cùng số, MỌI trạm.

    Kể cả trạm 0: trước đây trạm 0 cộng thêm nhóm "đã nhận chưa bàn giao" vào cùng
    con số, nên số của trạm 0 mang nghĩa khác số của năm trạm kia.
    """
    a = make_mo()
    make_mo()                 # lệnh thứ hai ở lại hàng chờ trạm 0
    flow.accept(a, 0)
    flow.handover(a)          # a sang hàng chờ trạm 1

    cho, _ = board_service.station_counts(db)
    for tram in STEP_NAMES:
        assert cho[tram] == len(_queue(db, tram)), f"trạm {tram}"

def test_badge_dang_giu_khop_at_station(db, make_mo, flow):
    """`holding` và `at_station` cũng phải là cùng một con số."""
    a = make_mo()
    flow.accept(a, 0)

    _, giu = board_service.station_counts(db)
    for tram in STEP_NAMES:
        assert giu[tram] == len(_at(db, tram)), f"trạm {tram}"

def test_viec_dang_lam_khong_bien_thanh_0(db, make_mo, flow):
    """Xưởng đang chạy mà mọi trạm hiện 0 — lỗi người dùng báo.

    Lệnh đã quét nhận thì RỜI hàng chờ. Nếu chỉ đếm hàng chờ thì ba lệnh đang lắp
    ráp ở trạm 4 hiện thành 0, và người đọc tưởng xưởng trống hoặc hệ thống hỏng.
    """
    for _ in range(3):
        code = make_mo()
        flow.accept(code, 0)
        flow.handover(code)
        flow.accept(code, 1)
        flow.accept(code, 2)
        flow.qc(code, "PASS")
        flow.accept(code, 3)
        flow.accept(code, 4)

    cho, giu = board_service.station_counts(db)
    assert all(n == 0 for n in cho.values()), "không lệnh nào còn chờ nhận"
    assert giu[4] == 3, "ba lệnh đang trong tay Sản xuất phải đếm được"
    assert sum(giu.values()) == 3

def test_tram_0_dem_rieng_hai_nhom(db, make_mo, flow):
    """Kho có hai nhóm rời nhau, và giờ chúng nằm ở hai con số khác nhau."""
    chua_nhan = make_mo()
    da_nhan = make_mo()
    flow.accept(da_nhan, 0)   # đã quét nhận, CHƯA bàn giao

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
    assert giu[0]["accepted_by"], "phải nói rõ ai đang giữ, không thì không truy được"
    assert giu[0]["holding_sec"] >= 0

def test_at_station_nha_lenh_khi_tram_sau_quet_nhan(db, make_mo, flow):
    """Bước chỉ đóng khi trạm SAU nhận — lúc đó lệnh phải rời khỏi trạm trước."""
    mo = make_mo()
    flow.accept(mo, 0)
    flow.handover(mo)
    flow.accept(mo, 1)

    assert mo not in [r["code"] for r in _at(db, 0)]
    assert mo in [r["code"] for r in _at(db, 1)]

def test_hang_doi_tram_3_chi_hien_lenh_QC_da_DAT(db, make_mo, flow):
    """Màn hình không được hứa thứ mà `guard_can_accept` sẽ chặn.

    QC quét nhận là bước 2 MỞ, chưa phải là đã phán. Liệt kê sớm thì Bàn team
    leader thấy lệnh, quét vào, và ăn lỗi `NO_QC` — lỗi không phải của họ.
    """
    mo = make_mo()
    flow.accept(mo, 0)
    flow.handover(mo)
    flow.accept(mo, 1)
    flow.accept(mo, 2)                      # QC đã NHẬN, chưa ra kết quả

    assert mo in [r["code"] for r in _at(db, 2)]
    assert mo not in [r["code"] for r in _queue(db, 3)]

    flow.qc(mo, "PASS")
    assert mo in [r["code"] for r in _queue(db, 3)]

def test_hang_doi_luon_co_waiting_sec(db, make_mo, flow):
    """Màn trạm hiện cột `chờ bao lâu` — thiếu trường là cả cột hiện dấu gạch."""
    mo = make_mo()
    flow.accept(mo, 0)
    flow.handover(mo)

    for tram in STEP_NAMES:
        for r in _queue(db, tram):
            assert "waiting_sec" in r, f"trạm {tram} thiếu waiting_sec"
            assert r["waiting_sec"] >= 0

def test_trace_KHONG_hoi_them_khi_MO_co_nhieu_vong(db, make_mo, flow):
    """Số câu SQL của `trace` phải KHÔNG đổi khi MO có thêm vòng.

    Trước khi gộp, mỗi vòng tốn thêm 5 câu: 1 vòng 10 câu, 4 vòng 25 câu. Test này
    đỏ ngay nếu ai đó đưa truy vấn trở lại vào trong vòng lặp.
    """
    code = make_mo()
    flow.accept(code, 0)
    flow.handover(code)
    flow.accept(code, 1)
    flow.accept(code, 2)

    db.flush()
    with dem_sql(db) as mot_vong:
        board_service.trace(db, code)

    flow.qc(code, "FAIL", reason="Sai thông số setup")   # đóng vòng 1, mở vòng 2
    assert flow.round_of(code).round_no == 2

    db.flush()
    with dem_sql(db) as hai_vong:
        board_service.trace(db, code)

    assert len(hai_vong) == len(mot_vong), (
        f"MO một vòng tốn {len(mot_vong)} câu, hai vòng tốn {len(hai_vong)} — "
        f"truy vấn đã lọt lại vào vòng lặp"
    )

def test_trace_van_tra_du_du_lieu_cua_tung_vong(db, make_mo, flow):
    """Gộp truy vấn mà ghép sai thì dữ liệu nhảy sang nhầm vòng — kiểm cả hai vòng."""
    code = make_mo()
    flow.accept(code, 0)
    flow.handover(code)
    flow.accept(code, 1)
    flow.accept(code, 2)
    flow.qc(code, "FAIL", reason="Sai thông số setup")

    cay = board_service.trace(db, code)
    assert len(cay["rounds"]) == 2

    vong1, vong2 = cay["rounds"]
    assert vong1["round_no"] == 1 and vong2["round_no"] == 2
    assert [s["step_no"] for s in vong1["steps"]] == [0, 1, 2]
    assert vong2["steps"] == []
    assert vong1["closed_at"] is not None and vong2["closed_at"] is None
    assert vong1["production"] is None and vong2["production"] is None
    assert vong1["packing"] is None and vong2["packing"] is None
