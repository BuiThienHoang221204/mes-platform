"""Báo cáo sản xuất — hai endpoint chỉ đọc.

Ba nhóm test, theo đúng thứ tự rủi ro:

1. **Một câu SQL, không N+1.** Đếm thẳng số câu lệnh chạy xuống CSDL và bắt nó
   KHÔNG tăng theo số lệnh sản xuất. Đây là thứ dễ hỏng âm thầm nhất: thêm một
   vòng lặp nhỏ trong service là báo cáo 100 lệnh thành 100 lượt đi về mà không
   test nghiệp vụ nào đỏ.
2. **Khung giờ trong SQL khớp từng giờ với khung trong Python.** Câu `CASE` sinh
   ra từ `shift.bins_of()`, nhưng "sinh ra từ" không đảm bảo "chạy giống" — phải
   cho cả 24 giờ đi qua cả hai đường rồi so.
3. **Bẫy A và Bẫy B** của `KE-HOACH-BAO-CAO-SAN-XUAT.md` §1.2.
"""

from __future__ import annotations

import uuid
from datetime import date

import pytest
from sqlalchemy import event, text

from app.common.errors import Invalid
from app.modules.reports import repository as reports_repo
from app.modules.reports import service as reports_service
from app.modules.reports import shift

NGAY = date(2026, 9, 15)
KHUNG = shift.BUCKETS

def _toi_chuyen(flow, code: str) -> None:
    flow.accept(code, 0)
    flow.handover(code)
    flow.accept(code, 1)
    flow.accept(code, 2)
    flow.qc(code, "PASS")
    flow.accept(code, 3)
    flow.accept(code, 4)
    flow.run_line(code, "L01")

def _bao_cao(db, bucket: int = 1, **kw):
    return reports_service.hourly(
        db, bucket=bucket, date_from=NGAY, date_to=NGAY, codes=None, **kw
    )

class _DemCau:
    """Đếm số câu lệnh gửi xuống CSDL trong một khối `with`."""

    def __init__(self, db):
        self.conn = db.get_bind()
        self.cau: list[str] = []

    def __enter__(self):
        event.listen(self.conn, "before_cursor_execute", self._ghi)
        return self

    def __exit__(self, *_):
        event.remove(self.conn, "before_cursor_execute", self._ghi)

    def _ghi(self, conn, cursor, statement, *a, **k):
        self.cau.append(statement)

@pytest.mark.parametrize("so_lenh", [1, 5])
def test_san_luong_gio_luon_MOT_cau_SQL_du_bao_nhieu_lenh(db, make_mo, flow, so_lenh):
    """Số lượt đi về CSDL KHÔNG được phụ thuộc số lệnh đang chạy.

    Trước khi có test này, cách viết tự nhiên nhất là lấy danh sách lệnh rồi hỏi
    sản lượng từng lệnh — 100 lệnh thành 101 câu. Mã lệnh nối sẵn trong cùng câu
    nên không có lượt hỏi thêm nào để đổi `round_id` ra `code`.
    """
    for _ in range(so_lenh):
        code = make_mo(qty=10_000, box=500)
        _toi_chuyen(flow, code)
        flow.hourly(code, 8, qty=500, people=10, target=600)
        flow.hourly(code, 14, qty=700, people=10, target=600)
    db.flush()

    with _DemCau(db) as dem:
        ra = _bao_cao(db, bucket=1)

    assert len(ra.series) == so_lenh
    assert len(dem.cau) == 1, f"{so_lenh} lệnh mà chạy {len(dem.cau)} câu SQL"

def test_tien_do_lenh_cung_chi_MOT_cau(db, make_mo, flow):
    for _ in range(3):
        _toi_chuyen(flow, make_mo(qty=5_000, box=500))
    db.flush()

    with _DemCau(db) as dem:
        page = reports_service.mo_progress(db, status=None, limit=50)

    assert len(page["items"]) >= 3
    assert page["total"] >= 3
    assert len(dem.cau) == 2

@pytest.mark.parametrize("bucket", KHUNG)
def test_khung_gio_trong_SQL_khop_khung_gio_trong_Python(db, bucket):
    """Cả 24 giờ đi qua hai đường rồi so — không chừa giờ nào.

    Đây là test bắt được đúng một lớp lỗi: giờ nghỉ trưa và giờ tăng ca. Chúng nằm
    NGOÀI mọi khung nên phải ghép vào khung gần nhất, và ghép về phía nào là chỗ
    hai bản cài đặt dễ nghĩ khác nhau.
    """
    sql = (
        f"SELECT g AS gio, ({reports_repo._bin_expr(bucket, 'g')}) AS khung, "
        f"NOT ({reports_repo._inside_expr(bucket, 'g')}) AS ngoai_khung "
        f"FROM generate_series(0, 23) AS g"
    )
    lech = [
        (r.gio, r.khung, shift.bin_of(r.gio, bucket), r.ngoai_khung, shift.is_folded(r.gio, bucket))
        for r in db.execute(text(sql)).all()
        if r.khung != shift.bin_of(r.gio, bucket) or r.ngoai_khung != shift.is_folded(r.gio, bucket)
    ]
    assert not lech, f"khung {bucket} giờ lệch ở: {lech}"

def test_gio_nghi_trua_ve_khung_buoi_SANG(db):
    """12:00 ở khung 4 giờ phải về `08–12`, không nhảy sang `13–17`."""
    r = shift.settings.report
    assert shift.bin_of(r.lunch_start, 4) == r.shift_start
    assert shift.bin_of(r.shift_end + 1, 4) == r.lunch_end

def test_khung_ca_om_tron_gio_nghi_trua(db):
    """Khung cả ca là `08–17`, nên 12:00 nằm TRONG nó — không tính là ngoài khung."""
    r = shift.settings.report
    assert shift.is_folded(r.lunch_start, r.shift_span) is False
    assert shift.is_folded(r.lunch_start, 4) is True

def test_gio_ket_thuc_lay_tu_dung_danh_sach_khung(db, make_mo, flow):
    """`at_end` phải nói đúng độ dài thật của khung, kể cả khung bị cắt ngắn."""
    code = make_mo(qty=10_000, box=500)
    _toi_chuyen(flow, code)
    flow.hourly(code, 9, qty=500, people=10, target=600)
    db.flush()

    diem = _bao_cao(db, bucket=4).series[0].points[0]
    khung = dict(shift.bins_of(4))
    assert diem.at.hour in khung
    assert diem.at_end.hour == khung[diem.at.hour] % 24

def test_gop_khung_cong_SO_THO_chu_khong_trung_binh_phan_tram(db, make_mo, flow):
    """Hai giờ trong cùng một khung: 500/1000 và 100/100.

    Trung bình hai phần trăm ra 75%. Cộng tử rồi cộng mẫu ra 600/1100 = 54,5%.
    Endpoint trả số thô nên phép chia chỉ xảy ra một lần, ở nơi vẽ.
    """
    code = make_mo(qty=10_000, box=500)
    _toi_chuyen(flow, code)
    flow.hourly(code, 8, qty=500, people=10, target=1_000)
    flow.hourly(code, 9, qty=100, people=10, target=100)
    db.flush()

    diem = _bao_cao(db, bucket=4).series[0].points
    assert len(diem) == 1, "hai giờ này phải rơi vào cùng một khung 4 giờ"
    assert (diem[0].qty, diem[0].target_qty, diem[0].slots) == (600, 1_100, 2)

def test_dong_thieu_dinh_muc_bi_loai_va_duoc_DEM_RA(db, make_mo, flow, actor):
    """Dòng cũ từ trước migration `0006` không có `target_qty`.

    Coi nó là 0 thì phép chia nổ; lặng lẽ bỏ đi thì người xem tưởng giờ đó không
    ai làm. Phải loại khỏi phép tính NHƯNG đếm ra màn hình.
    """
    code = make_mo(qty=10_000, box=500)
    _toi_chuyen(flow, code)
    flow.hourly(code, 8, qty=500, people=10, target=600)
    rnd = flow.round_of(code)
    db.execute(
        text("INSERT INTO hourly_output (id, round_id, work_date, slot_hour, qty,"
             "                           target_qty, recorded_by)"
             " VALUES (:i, :r, :d, 9, 400, NULL, :u)"),
        {"i": uuid.uuid4(), "r": rnd.id, "d": NGAY, "u": actor},
    )
    db.flush()

    ra = _bao_cao(db, bucket=1)
    assert ra.skipped_rows == 1
    assert sum(p.qty for s in ra.series for p in s.points) == 500, "dòng thiếu đã lọt vào tử số"

def test_ca_khoang_ngay_thieu_dinh_muc_thi_van_dem_duoc(db, make_mo, flow, actor):
    """Không còn dòng nào để gộp — con số `đã bỏ n dòng` vẫn phải về.

    Đây là lý do câu SQL viết `tally LEFT JOIN grouped` chứ không lọc thẳng: lọc
    thẳng thì phần gộp rỗng kéo theo cả hai bộ đếm biến mất, đúng lúc chúng cần nhất.
    """
    code = make_mo(qty=10_000, box=500)
    _toi_chuyen(flow, code)
    rnd = flow.round_of(code)
    db.execute(
        text("INSERT INTO hourly_output (id, round_id, work_date, slot_hour, qty,"
             "                           target_qty, recorded_by)"
             " VALUES (:i, :r, :d, 9, 400, NULL, :u)"),
        {"i": uuid.uuid4(), "r": rnd.id, "d": NGAY, "u": actor},
    )
    db.flush()

    ra = _bao_cao(db, bucket=1)
    assert ra.series == []
    assert ra.skipped_rows == 1

def test_gio_tang_ca_khong_bi_bo_di_ma_duoc_dem_ra(db, make_mo, flow):
    """Ghi lúc 18:00 — ngoài giờ đi làm. Tổng phải giữ nguyên, và phải có lời nhắc."""
    code = make_mo(qty=10_000, box=500)
    _toi_chuyen(flow, code)
    flow.hourly(code, 8, qty=500, people=10, target=600)
    flow.hourly(code, 18, qty=300, people=4, target=400)
    db.flush()

    gop = _bao_cao(db, bucket=4)
    assert sum(p.qty for s in gop.series for p in s.points) == 800, "mất hàng của giờ tăng ca"
    assert gop.folded_rows == 1

    gio = _bao_cao(db, bucket=1)
    assert gio.folded_rows == 0, "khung 1 giờ trải cả ngày nên không đẩy ai đi đâu"

def test_khoang_ngay_qua_dai_thi_chan(db):
    from app.common.config import settings

    with pytest.raises(Invalid) as e:
        reports_service.hourly(
            db, bucket=1, date_from=date(2020, 1, 1), date_to=date(2026, 1, 1), codes=None
        )
    assert str(settings.report.max_days) in str(e.value)

def test_ngay_bat_dau_sau_ngay_ket_thuc_thi_chan(db):
    with pytest.raises(Invalid):
        reports_service.hourly(
            db, bucket=1, date_from=date(2026, 9, 20), date_to=date(2026, 9, 1), codes=None
        )

def test_qua_nhieu_ma_lenh_thi_chan(db):
    from app.common.config import settings

    qua = [f"M{i:06d}" for i in range(settings.report.max_codes + 1)]
    with pytest.raises(Invalid):
        reports_service.hourly(db, bucket=1, date_from=NGAY, date_to=NGAY, codes=qua)

def test_khung_gop_la_thi_chan(db):
    with pytest.raises(Invalid) as e:
        reports_service.hourly(db, bucket=3, date_from=NGAY, date_to=NGAY, codes=None)
    assert "3" in str(e.value)

def test_limit_bi_kep_tran(db, make_mo, flow):
    from app.common.config import settings

    for _ in range(3):
        _toi_chuyen(flow, make_mo(qty=5_000, box=500))
    db.flush()
    page = reports_service.mo_progress(db, status=None, limit=10**9)
    assert len(page["items"]) <= settings.report.max_rows


# ══ Lọc theo ngày tạo lệnh ═════════════════════════════════════════════════
def test_tien_do_loc_theo_ngay_tao_lenh(db, make_mo):
    from datetime import date, timedelta

    from app.modules.reports import service as reports_service

    make_mo()
    hom_nay = date.today()

    trong = reports_service.mo_progress(
        db, status=None, limit=50, date_from=hom_nay, date_to=hom_nay
    )
    assert trong["total"] >= 1

    xa = hom_nay - timedelta(days=400)
    ngoai = reports_service.mo_progress(
        db, status=None, limit=50, date_from=xa, date_to=xa
    )
    assert ngoai["total"] == 0
    assert ngoai["items"] == []


def test_tien_do_khong_loc_thi_dem_het(db, make_mo):
    from app.modules.reports import service as reports_service

    make_mo()
    assert reports_service.mo_progress(db, status=None, limit=50)["total"] >= 1


def test_tien_do_KHONG_muon_tran_31_ngay_cua_bao_cao_gio(db, make_mo):
    """Trần `max_days` sinh ra cho `hourly` vì chỗ đó quét theo từng ngày.

    Tiến độ lệnh lọc `created_at` rồi `LIMIT` nên 80 ngày không đắt hơn 1 ngày.
    """
    from datetime import date, timedelta

    from app.common.config import settings
    from app.modules.reports import service as reports_service

    make_mo()
    hom_nay = date.today()
    rong = hom_nay - timedelta(days=settings.report.max_days + 50)

    ra = reports_service.mo_progress(db, status=None, limit=50,
                                     date_from=rong, date_to=hom_nay)
    assert ra["total"] >= 1


def test_tien_do_chan_ngay_dao_nguoc(db):
    from datetime import date, timedelta

    import pytest

    from app.common.errors import Invalid
    from app.modules.reports import service as reports_service

    hom_nay = date.today()
    with pytest.raises(Invalid):
        reports_service.mo_progress(db, status=None, limit=50,
                                    date_from=hom_nay, date_to=hom_nay - timedelta(days=3))


def test_bao_cao_gio_VAN_giu_tran_31_ngay(db):
    from datetime import date, timedelta

    import pytest

    from app.common.config import settings
    from app.common.errors import Invalid
    from app.modules.reports import service as reports_service

    hom_nay = date.today()
    qua_dai = hom_nay - timedelta(days=settings.report.max_days + 5)
    with pytest.raises(Invalid):
        reports_service.hourly(db, bucket=1, date_from=qua_dai, date_to=hom_nay, codes=None)
