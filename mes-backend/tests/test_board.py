"""Màn hình điều hành: con số phải khớp danh sách, và số câu SQL không được tăng.

Hai loại lỗi ở đây đều KHÔNG làm test nào khác đỏ:

* Badge hiện một số, bấm vào ra số khác — vì câu đếm và câu liệt kê trôi khỏi nhau.
* `trace` hỏi CSDL từng vòng một — chạy vẫn đúng, chỉ là chậm dần theo số vòng.
"""

from __future__ import annotations

from contextlib import contextmanager

from sqlalchemy import event, text

from app.common.vocab.enums import STEP_NAMES
from app.modules.board import repository as board_repo
from app.modules.board import service as board_service


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


# ── Badge và danh sách phải là một ──────────────────────────────────────────


def test_badge_khop_danh_sach(db, make_mo, flow):
    """`station_counts` và `queue` dựng từ cùng một nguồn SQL — phải ra cùng số."""
    a = make_mo()
    make_mo()                 # lệnh thứ hai ở lại hàng chờ trạm 0
    flow.accept(a, 0)
    flow.handover(a)          # a sang hàng chờ trạm 1

    dem = board_service.station_counts(db)
    for tram in STEP_NAMES:
        if tram == 0:
            continue          # trạm 0 cộng thêm nhóm riêng, kiểm ở ca dưới
        assert dem[tram] == len(board_service.queue(db, tram)), f"trạm {tram}"


def test_badge_tram_0_dem_CA_lenh_da_nhan_chua_ban_giao(db, make_mo, flow):
    """Chỉ đếm nhóm chưa ai nhận thì badge hiện 0 trong khi kho còn hàng nằm đó."""
    chua_nhan = make_mo()
    da_nhan = make_mo()
    flow.accept(da_nhan, 0)   # đã quét nhận, CHƯA bàn giao

    cho_ban_giao = db.execute(text(board_repo.CHO_BAN_GIAO_SQL)).scalar_one()
    assert cho_ban_giao >= 1, "phải có ít nhất lệnh vừa quét nhận"

    dem = board_service.station_counts(db)
    assert dem[0] == len(board_service.queue(db, 0)) + cho_ban_giao
    assert chua_nhan in [r["code"] for r in board_service.queue(db, 0)]


def test_at_station_la_viec_DANG_cam_khong_phai_hang_doi(db, make_mo, flow):
    """Hai danh sách phải rời nhau: nhận rồi thì rời hàng đợi, sang `at_station`."""
    mo = make_mo()
    assert mo in [r["code"] for r in board_service.queue(db, 0)]
    assert mo not in [r["code"] for r in board_service.at_station(db, 0)]

    flow.accept(mo, 0)
    assert mo not in [r["code"] for r in board_service.queue(db, 0)]
    giu = [r for r in board_service.at_station(db, 0) if r["code"] == mo]
    assert len(giu) == 1
    assert giu[0]["accepted_by"], "phải nói rõ ai đang giữ, không thì không truy được"
    assert giu[0]["holding_sec"] >= 0


def test_at_station_nha_lenh_khi_tram_sau_quet_nhan(db, make_mo, flow):
    """Bước chỉ đóng khi trạm SAU nhận — lúc đó lệnh phải rời khỏi trạm trước."""
    mo = make_mo()
    flow.accept(mo, 0)
    flow.handover(mo)
    flow.accept(mo, 1)

    assert mo not in [r["code"] for r in board_service.at_station(db, 0)]
    assert mo in [r["code"] for r in board_service.at_station(db, 1)]


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

    assert mo in [r["code"] for r in board_service.at_station(db, 2)]
    assert mo not in [r["code"] for r in board_service.queue(db, 3)]

    flow.qc(mo, "PASS")
    assert mo in [r["code"] for r in board_service.queue(db, 3)]


def test_hang_doi_luon_co_waiting_sec(db, make_mo, flow):
    """Màn trạm hiện cột `chờ bao lâu` — thiếu trường là cả cột hiện dấu gạch."""
    mo = make_mo()
    flow.accept(mo, 0)
    flow.handover(mo)

    for tram in STEP_NAMES:
        for r in board_service.queue(db, tram):
            assert "waiting_sec" in r, f"trạm {tram} thiếu waiting_sec"
            assert r["waiting_sec"] >= 0


# ── Không được quay lại N+1 ─────────────────────────────────────────────────


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

    # Đẩy hết thay đổi đang treo xuống TRƯỚC khi đo: fixture test bật autoflush,
    # không flush thì câu ghi của bước dựng dữ liệu bị tính vào số của `trace`.
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
    # Vòng 1 đã đi qua ba trạm; vòng 2 vừa mở nên chưa trạm nào nhận.
    assert [s["step_no"] for s in vong1["steps"]] == [0, 1, 2]
    assert vong2["steps"] == []
    assert vong1["closed_at"] is not None and vong2["closed_at"] is None
    # Chưa vòng nào chốt sổ hay đóng thùng → phải là None, không phải nhặt nhầm của vòng kia
    assert vong1["production"] is None and vong2["production"] is None
    assert vong1["packing"] is None and vong2["packing"] is None
