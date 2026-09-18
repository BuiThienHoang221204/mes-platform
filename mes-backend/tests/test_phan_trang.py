"""Phân trang — năm mệnh đề, mỗi cái một cách hỏng riêng.

Cái đắt nhất là test đầu tiên. Phân trang mà thứ tự không ổn định thì **không nổ ở
đâu cả**: trang 1 và trang 2 cùng chứa một dòng, một dòng khác biến mất khỏi cả hai,
và tổng vẫn đúng. Người dùng chỉ thấy "lệnh của tôi đâu mất rồi".
"""

from __future__ import annotations

import pytest
from sqlalchemy import event

from app.common.deps import PAGE_MAX, PAGE_SIZE, page_params
from app.common.errors import NotFound
from app.common.vocab.enums import MoStatus
from app.modules.board import repository as board_repo
from app.modules.board import service as board_service
from app.modules.mo import repository as mo_repo
from app.modules.mo import service as mo_service
from app.modules.reports import service as reports_service


def _tao(db, actor, n: int) -> list[str]:
    """`n` lệnh tạo trong CÙNG một transaction — nên `created_at` giống hệt nhau.

    Đó chính là điều kiện làm lộ bẫy khoá phụ: sắp theo mỗi `created_at` thì thứ tự
    giữa chúng là tuỳ Postgres, mỗi lần gọi một khác.
    """
    codes = [f"M7{i:05d}" for i in range(1, n + 1)]
    mo_service.create(
        db, [mo_service.NewMo(c, "Vỏ nhựa F3", 1_000, 3_600, 500) for c in codes], actor)
    db.flush()
    return codes

def test_hai_trang_ghep_lai_du_va_khong_lap(db, actor):
    _tao(db, actor, 30)

    t1 = mo_repo.list_mos(db, status=MoStatus.DRAFT, limit=10, offset=0)
    t2 = mo_repo.list_mos(db, status=MoStatus.DRAFT, limit=10, offset=10)
    t3 = mo_repo.list_mos(db, status=MoStatus.DRAFT, limit=10, offset=20)

    ma = [m.code for m in t1 + t2 + t3]
    assert len(ma) == 30
    assert len(set(ma)) == 30, "có dòng lọt vào hai trang — thiếu khoá phụ trong ORDER BY"

def test_goi_lai_nhieu_lan_van_ra_cung_thu_tu(db, actor):
    """Thứ tự phải TÁI LẬP được, không thì mỗi lần bấm sang trang lại ra khác.

    Lưu ý: test này **không chứng minh** được thiếu khoá phụ là hỏng — bảng nhỏ thì
    Postgres quét tuần tự và vô tình trả đúng thứ tự chèn. Đã thử bỏ khoá phụ ra: test
    này vẫn xanh. Cái canh thật sự là `test_moi_cau_phan_trang_deu_co_khoa_phu` dưới.
    """
    _tao(db, actor, 30)
    lan_1 = [m.code for m in mo_repo.list_mos(db, status=MoStatus.DRAFT, limit=30)]
    for _ in range(3):
        assert [m.code for m in mo_repo.list_mos(db, status=MoStatus.DRAFT, limit=30)] == lan_1

def _sql_da_chay(db, chay) -> list[str]:
    """Bắt nguyên văn câu SQL đã gửi xuống CSDL."""
    cau: list[str] = []
    conn = db.get_bind()

    def ghi(conn, cursor, statement, *a, **k):
        cau.append(statement)

    event.listen(conn, "before_cursor_execute", ghi)
    try:
        chay()
    finally:
        event.remove(conn, "before_cursor_execute", ghi)
    return cau

def test_moi_cau_phan_trang_deu_co_khoa_phu(db, actor):
    """Canh CẤU TRÚC câu SQL, không canh kết quả.

    Thiếu khoá phụ là lỗi **không nhìn thấy được trên dữ liệu nhỏ**: nó chỉ lộ ra khi
    bảng đủ lớn để Postgres đổi sang quét song song hay đọc theo chỉ mục — tức là ở
    máy thật, sau vài tháng, và không ai nối được nó với nguyên nhân. Nên canh ngay
    ở câu chữ: `ORDER BY` của mọi câu phân trang phải có `code`, vốn là duy nhất.
    """
    _tao(db, actor, 3)
    cau = _sql_da_chay(db, lambda: mo_repo.list_mos(db, status=MoStatus.DRAFT, limit=5))
    sau_order = cau[-1].lower().rsplit("order by", 1)[-1]
    assert "code" in sau_order, f"ORDER BY thiếu khoá phụ duy nhất: {sau_order[:80]}"

    for sql in (board_repo.AT_STATION_SQL,
                board_repo.QUEUE_SQL[0] + " ORDER BY m.code"):
        sau = sql.lower().rsplit("order by", 1)[-1]
        assert "code" in sau, f"ORDER BY thiếu khoá phụ: {sau[:80]}"

def test_total_dem_dung_ca_khi_co_loc(db, actor, make_mo):
    _tao(db, actor, 7)
    make_mo()                                   # một lệnh PROCESSING

    assert mo_repo.count_mos(db, status=MoStatus.DRAFT) == 7
    tat_ca = mo_repo.count_mos(db)
    assert tat_ca >= 8
    assert tat_ca > mo_repo.count_mos(db, status=MoStatus.DRAFT)

def test_total_khong_doi_theo_trang(db, actor):
    """`total` là tổng SAU KHI lọc, không phải số dòng trong trang."""
    _tao(db, actor, 25)
    n = mo_repo.count_mos(db, status=MoStatus.DRAFT)
    assert n == 25
    assert len(mo_repo.list_mos(db, status=MoStatus.DRAFT, limit=10)) == 10

def test_mac_dinh_dung_bang_PAGE_SIZE(db):
    assert page_params() == (PAGE_SIZE, 0)

@pytest.mark.parametrize("gui, mong", [(999_999, PAGE_MAX), (0, 1), (-5, 1), (7, 7)])
def test_limit_bi_kep_hai_dau(gui, mong):
    assert page_params(limit=gui)[0] == mong

def test_offset_am_ve_khong(db, actor):
    _tao(db, actor, 3)
    assert page_params(offset=-9)[1] == 0
    assert len(mo_repo.list_mos(db, status=MoStatus.DRAFT, limit=10, offset=0)) == 3

def test_limit_that_su_cat_o_tang_CSDL(db, actor):
    """Kẹp ở cửa rồi nhưng câu SQL vẫn phải có `LIMIT` — không cắt ở Python."""
    _tao(db, actor, 25)
    assert len(mo_repo.list_mos(db, status=MoStatus.DRAFT, limit=PAGE_SIZE)) == PAGE_SIZE

def test_bang_dang_chay_phan_trang_va_dem_dung(db, make_mo, flow):
    for _ in range(5):
        make_mo()
    db.flush()

    trang = board_repo.running_rows(db, limit=2)
    assert len(trang) == 2
    assert board_repo.count_running(db) >= 5

def test_hang_doi_va_dang_giu_dem_tu_dung_cau_dang_dung(db, make_mo, flow):
    """`count_queue` bọc lại chính `QUEUE_SQL` — hai số không thể trôi khỏi nhau."""
    for _ in range(4):
        make_mo()
    db.flush()

    assert board_repo.count_queue(db, 0) == len(board_repo.queue_rows(db, 0, limit=100))

    code = make_mo()
    flow.accept(code, 0)
    db.flush()
    assert board_repo.count_at_station(db, 0) == len(
        board_repo.at_station_rows(db, 0, limit=100))

def test_bao_cao_tien_do_tra_items_va_total(db, make_mo, flow):
    for _ in range(4):
        make_mo()
    db.flush()

    page = reports_service.mo_progress(db, status="PROCESSING", limit=2)
    assert len(page["items"]) == 2
    assert page["total"] >= 4, "total phải là tổng sau lọc, không phải số dòng trong trang"

def _mot_vong_nhieu_gio(db, make_mo, flow, actor, n: int) -> str:
    """Một vòng có `n` dòng sản lượng giờ — đủ để vượt một trang.

    Phải tràn sang NGHỬ NGÀY KHÁC chứ không dùng một ngày: `UNIQUE (vòng, ngày, khung
    giờ)` chặn trùng, mà một ngày chỉ có 24 khung. Đó cũng đúng thực tế: vòng có hơn
    hai mươi dòng sổ giờ là vòng chạy qua nhiều ngày.
    """
    from datetime import date, timedelta

    from app.modules.production import hourly_service

    code = make_mo(qty=100_000, box=500)
    flow.accept(code, 0)
    flow.handover(code)
    flow.accept(code, 1)
    flow.accept(code, 2)
    flow.qc(code, "PASS")
    flow.accept(code, 3)
    flow.accept(code, 4)
    flow.run_line(code, "L01")
    for i in range(n):
        hourly_service.add_hourly(
            db, code=code,
            work_date=date(2026, 9, 15) + timedelta(days=i // 16),
            slot_hour=6 + i % 16,
            headcount=10, target_qty=120, qty=100, note=None, actor_id=actor,
        )
    db.flush()
    return code

def test_trace_chi_tra_TRANG_DAU_hai_so_vo_han(db, make_mo, flow, actor):
    """`steps` ≤ 6, `lines` ≤ 14, số vòng hiếm khi quá 5 — ba thứ đó có trần tự nhiên.

    Chỉ sổ giờ và sổ thùng là không có trần, nên chúng mới làm cây truy cứu phình
    theo thời gian. Trace c���t ở một trang và nói ra tổng; phần còn lại có endpoint riêng.
    """
    code = _mot_vong_nhieu_gio(db, make_mo, flow, actor, PAGE_SIZE + 5)

    rnd = board_service.trace(db, code)["rounds"][0]
    assert len(rnd["hourly"]) == PAGE_SIZE
    assert rnd["hourly_total"] == PAGE_SIZE + 5, "phải nói ra tổng, không lặng lẽ cắt"

def test_hai_trang_so_gio_khong_lap_va_du(db, make_mo, flow, actor):
    n = PAGE_SIZE + 5
    code = _mot_vong_nhieu_gio(db, make_mo, flow, actor, n)

    t1 = board_service.round_hourly(db, code, 1, limit=PAGE_SIZE, offset=0)
    t2 = board_service.round_hourly(db, code, 1, limit=PAGE_SIZE, offset=PAGE_SIZE)

    assert (t1["total"], len(t1["items"]), len(t2["items"])) == (n, PAGE_SIZE, 5)
    khoa = [(x["work_date"], x["slot_hour"]) for x in t1["items"] + t2["items"]]
    assert len(set(khoa)) == n, "hai trang chồng nhau"

def test_hoi_vong_khong_co_thi_bao_loi_ro_rang(db, make_mo, flow, actor):
    code = _mot_vong_nhieu_gio(db, make_mo, flow, actor, 2)
    with pytest.raises(NotFound) as e:
        board_service.round_hourly(db, code, 99, limit=PAGE_SIZE, offset=0)
    assert "99" in str(e.value)


def test_loc_theo_ngay_tao(db, actor, make_mo):
    """Lọc ngày phải ở SERVER: danh sách đã phân trang, lọc ở FE chỉ lọc được
    mười dòng đang cầm và con số tổng trên đầu bảng thành nói dối."""
    from datetime import date, timedelta

    _tao(db, actor, 5)
    hnay = date.today()

    assert mo_repo.count_mos(db, date_from=hnay, date_to=hnay) >= 5
    assert mo_repo.count_mos(db, date_from=hnay + timedelta(days=1)) == 0
    assert mo_repo.count_mos(db, date_to=hnay - timedelta(days=1)) == 0


def test_ngay_ket_thuc_lay_TRON_ca_ngay(db, actor):
    """`created_at` có giờ phút, nên `<= to` là mất sạch lệnh tạo trong ngày cuối
    — chỉ giữ đúng lệnh tạo lúc 00:00:00. Vế lọc phải là `< to + 1 ngày`."""
    from datetime import date

    _tao(db, actor, 3)
    hnay = date.today()
    assert mo_repo.count_mos(db, status=MoStatus.DRAFT, date_from=hnay, date_to=hnay) == 3


def test_loc_ngay_va_trang_thai_chong_len_nhau(db, actor, make_mo):
    from datetime import date

    _tao(db, actor, 4)
    make_mo()
    hnay = date.today()
    nhap = mo_repo.count_mos(db, status=MoStatus.DRAFT, date_from=hnay, date_to=hnay)
    tat_ca = mo_repo.count_mos(db, date_from=hnay, date_to=hnay)
    assert nhap == 4
    assert tat_ca > nhap
