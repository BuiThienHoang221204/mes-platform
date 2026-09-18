"""Mỗi ràng buộc trong DB-GON.md phải THẬT SỰ chặn.

Đợt 1 của BE-PLAN: viết nhóm test này TRƯỚC khi có service nào. Ràng buộc nào
không có test ở đây là ràng buộc chưa được chứng minh là hoạt động.
"""

from __future__ import annotations

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError, IntegrityError

from app.common.errors import translate_db_error
from app.modules.mo.models import ManufacturingOrder
from app.modules.production.models import Production
from app.modules.round.models import MoRound


def _mo(db, actor, code="M111111", qty=10_000) -> ManufacturingOrder:
    mo = ManufacturingOrder(code=code, product_name="X", quantity=qty,
                            required_production_sec=10_800, created_by=actor)
    db.add(mo)
    db.flush()
    return mo


def _round(db, mo, no=1, target=None) -> MoRound:
    rnd = MoRound(mo_id=mo.id, round_no=no, target_qty=target or mo.quantity,
                  required_sec=10_800)
    db.add(rnd)
    db.flush()
    return rnd


# ══ Lệnh sản xuất ═══════════════════════════════════════════════════════════
def test_ma_mo_sai_dinh_dang_bi_chan(db, actor):
    """§2.2 — chặn ngay ở DB, không chỉ ở tầng ứng dụng."""
    db.add(ManufacturingOrder(code="F3-25/06-001", product_name="X", quantity=1,
                              required_production_sec=60, created_by=actor))
    with pytest.raises(IntegrityError) as e:
        db.flush()
    assert translate_db_error(e.value).code == "MO_CODE"


def test_huy_lenh_khong_co_ly_do_bi_chan(db, actor):
    mo = _mo(db, actor)
    mo.status = "CANCELLED"
    with pytest.raises(IntegrityError) as e:
        db.flush()
    assert translate_db_error(e.value).code == "CANCEL_REASON"


def test_khoa_cung_sau_submit(db, actor):
    """§4A — trigger mo_lock_after_submit."""
    mo = _mo(db, actor)
    mo.status = "PROCESSING"
    db.flush()
    mo.quantity = 5
    with pytest.raises(DBAPIError) as e:
        db.flush()
    assert translate_db_error(e.value).code == "MO_LOCKED"


# ══ Vòng chạy ═══════════════════════════════════════════════════════════════
def test_moi_don_chi_mot_vong_dang_mo(db, actor):
    """§6b — chỉ mục duy nhất một phần mo_round_one_open."""
    mo = _mo(db, actor)
    _round(db, mo, 1)
    # `_round` tự flush, nên lỗi bật ra NGAY tại lời gọi — phải bọc chính nó,
    # không phải bọc một `db.flush()` đứng sau.
    with pytest.raises(IntegrityError) as e:
        _round(db, mo, 2)
    assert translate_db_error(e.value).code == "ROUND_OPEN"


def test_returned_to_step_chi_nhan_0_hoac_3(db, actor):
    mo = _mo(db, actor)
    rnd = _round(db, mo)
    rnd.returned_to_step = 4
    with pytest.raises(IntegrityError):
        db.flush()


# ══ Chốt sổ Sản xuất — §7.5 ═════════════════════════════════════════════════
def test_ba_so_phai_cong_dung_bang_muc_tieu_vong(db, actor):
    mo = _mo(db, actor, qty=10_000)
    rnd = _round(db, mo)
    db.add(Production(round_id=rnd.id, qty_ok=9_000, qty_ng=500, qty_short=300,
                      ng_reason_text="x", short_reason_text="y", closed_by=actor))
    with pytest.raises(DBAPIError) as e:
        db.flush()
    err = translate_db_error(e.value)
    assert err.code == "PROD_BALANCE"
    assert "9800" in err.message.replace(".", "") or "9 800" in err.message


def test_ba_so_cong_dung_thi_ghi_duoc(db, actor):
    mo = _mo(db, actor, qty=10_000)
    rnd = _round(db, mo)
    db.add(Production(round_id=rnd.id, qty_ok=9_000, qty_ng=500, qty_short=500,
                      ng_reason_text="Hư máy", short_reason_text="Chờ bù liệu",
                      closed_by=actor))
    db.flush()


def test_co_hong_ma_khong_ghi_ly_do_bi_chan(db, actor):
    mo = _mo(db, actor, qty=1_000)
    rnd = _round(db, mo)
    db.add(Production(round_id=rnd.id, qty_ok=900, qty_ng=100, qty_short=0, closed_by=actor))
    with pytest.raises(IntegrityError) as e:
        db.flush()
    assert translate_db_error(e.value).code == "NG_REASON"


def test_lam_thieu_ma_khong_ghi_ly_do_bi_chan(db, actor):
    mo = _mo(db, actor, qty=1_000)
    rnd = _round(db, mo)
    db.add(Production(round_id=rnd.id, qty_ok=900, qty_ng=0, qty_short=100, closed_by=actor))
    with pytest.raises(IntegrityError) as e:
        db.flush()
    assert translate_db_error(e.value).code == "SHORT_REASON"


def test_chot_so_sx_mot_lan_roi_thoi(db, actor):
    """RULE production_no_update — lần sửa thứ hai không ghi được gì."""
    mo = _mo(db, actor, qty=1_000)
    rnd = _round(db, mo)
    db.add(Production(round_id=rnd.id, qty_ok=1_000, qty_ng=0, qty_short=0, closed_by=actor))
    db.flush()
    db.execute(text("UPDATE production SET qty_ok = 1 WHERE round_id = :r"), {"r": rnd.id})
    still = db.execute(
        text("SELECT qty_ok FROM production WHERE round_id = :r"), {"r": rnd.id}
    ).scalar_one()
    assert still == 1_000  # RULE nuốt lệnh UPDATE, số cũ còn nguyên


# ══ Đóng thùng — §7b ══════════════════════════════════════════════════════════
def test_dong_goi_vuot_sl_dat_bi_chan(db, actor):
    mo = _mo(db, actor, qty=1_000)
    rnd = _round(db, mo)
    db.add(Production(round_id=rnd.id, qty_ok=800, qty_ng=0, qty_short=200,
                      short_reason_text="hết ca", closed_by=actor))
    db.flush()
    with pytest.raises(DBAPIError) as e:
        db.execute(
            text(
                """
                INSERT INTO packing (round_id, started_by, qty_packed, completed_at, completed_by)
                VALUES (:r, :u, 900, now(), :u)
                """
            ),
            {"r": rnd.id, "u": actor},
        )
    assert translate_db_error(e.value).code == "PACK_OVER_OK"


def test_dong_goi_khi_chua_chot_so_sx_bi_chan(db, actor):
    mo = _mo(db, actor, qty=1_000)
    rnd = _round(db, mo)
    with pytest.raises(DBAPIError) as e:
        db.execute(
            text(
                """
                INSERT INTO packing (round_id, started_by, qty_packed, completed_at, completed_by)
                VALUES (:r, :u, 100, now(), :u)
                """
            ),
            {"r": rnd.id, "u": actor},
        )
    assert translate_db_error(e.value).code == "PACK_BEFORE_PROD"


# ══ Đoạn chuyền — §14B, §17 ═════════════════════════════════════════════════
def test_mot_chuyen_chay_hai_mo_cung_luc_thi_DUOC(db, actor):
    """§14B — chuyền là dây chuyền có N chỗ ngồi, không phải một cái máy.

    Lệnh ít linh kiện chỉ dùng 5 trong 10 chỗ; 5 người còn lại ngồi làm lệnh khác
    ngay trên chuyền đó. Bản 0001 chặn bằng `line_run_no_overlap`, migration 0008 gỡ.
    """
    a = _round(db, _mo(db, actor, code="M222222"))
    b = _round(db, _mo(db, actor, code="M333333"))
    ins = text(
        """
        INSERT INTO line_segment (round_id, line_id, kind, started_at, started_by)
        VALUES (:r, 1, 'RUN', now(), :u)
        """
    )
    db.execute(ins, {"r": a.id, "u": actor})
    db.execute(ins, {"r": b.id, "u": actor})

    n = db.execute(
        text("SELECT count(*) FROM line_segment WHERE line_id = 1 AND ended_at IS NULL")
    ).scalar_one()
    assert n == 2, "hai lệnh cùng chạy trên một chuyền"


def test_mot_chuyen_chay_nhieu_mo_KHAC_gio_thi_duoc(db, actor):
    """§14B — chỉ chặn CHỒNG GIỜ, không chặn dùng chung chuyền."""
    a = _round(db, _mo(db, actor, code="M444444"))
    b = _round(db, _mo(db, actor, code="M555555"))
    db.execute(
        text(
            """
            INSERT INTO line_segment (round_id, line_id, kind, started_at, ended_at, started_by)
            VALUES (:r, 2, 'RUN', now() - interval '2 hour', now() - interval '1 hour', :u)
            """
        ),
        {"r": a.id, "u": actor},
    )
    db.execute(
        text(
            """
            INSERT INTO line_segment (round_id, line_id, kind, started_at, started_by)
            VALUES (:r, 2, 'RUN', now(), :u)
            """
        ),
        {"r": b.id, "u": actor},
    )


def test_ly_do_dung_chi_gan_voi_doan_cho(db, actor):
    rnd = _round(db, _mo(db, actor, code="M666666"))
    with pytest.raises(IntegrityError) as e:
        db.execute(
            text(
                """
                INSERT INTO line_segment
                  (round_id, line_id, kind, started_by, hold_reason_text)
                VALUES (:r, 3, 'RUN', :u, 'hư máy')
                """
            ),
            {"r": rnd.id, "u": actor},
        )
    assert translate_db_error(e.value).code == "SEG_REASON"


# ══ Sản lượng giờ — §7.2b ═══════════════════════════════════════════════════
def test_moi_khung_gio_moi_ngay_chi_ghi_mot_lan(db, actor):
    rnd = _round(db, _mo(db, actor, code="M777777"))
    ins = text(
        """
        INSERT INTO hourly_output (round_id, work_date, slot_hour, qty, recorded_by)
        VALUES (:r, DATE '2026-09-13', 8, :q, :u)
        """
    )
    db.execute(ins, {"r": rnd.id, "q": 500, "u": actor})
    with pytest.raises(IntegrityError) as e:
        db.execute(ins, {"r": rnd.id, "q": 300, "u": actor})
    assert translate_db_error(e.value).code == "HOURLY_DUP"


def test_cung_khung_gio_KHAC_ngay_thi_ghi_duoc(db, actor):
    """MO chạy qua đêm vẫn ghi được khung 08:00-09:00 của hôm sau."""
    rnd = _round(db, _mo(db, actor, code="M888888"))
    for d in ("2026-09-13", "2026-09-14"):
        db.execute(
            text(
                """
                INSERT INTO hourly_output (round_id, work_date, slot_hour, qty, recorded_by)
                VALUES (:r, CAST(:d AS date), 8, 500, :u)
                """
            ),
            {"r": rnd.id, "d": d, "u": actor},
        )


def test_tong_san_luong_gio_khong_vuot_muc_tieu_vong(db, actor):
    rnd = _round(db, _mo(db, actor, code="M999999", qty=1_000), target=1_000)
    with pytest.raises(DBAPIError) as e:
        db.execute(
            text(
                """
                INSERT INTO hourly_output (round_id, work_date, slot_hour, qty, recorded_by)
                VALUES (:r, DATE '2026-09-13', 9, 1500, :u)
                """
            ),
            {"r": rnd.id, "u": actor},
        )
    assert translate_db_error(e.value).code == "HOURLY_OVER"


# ══ Nhật ký — §25A ══════════════════════════════════════════════════════════
def test_nhat_ky_khong_sua_khong_xoa(db, actor):
    mo = _mo(db, actor, code="M121212")
    db.execute(
        text("INSERT INTO mo_event (mo_id, action) VALUES (:m, 'TEST')"), {"m": mo.id}
    )
    db.execute(text("UPDATE mo_event SET action = 'HACKED' WHERE mo_id = :m"), {"m": mo.id})
    db.execute(text("DELETE FROM mo_event WHERE mo_id = :m"), {"m": mo.id})
    rows = db.execute(
        text("SELECT action FROM mo_event WHERE mo_id = :m"), {"m": mo.id}
    ).scalars().all()
    assert rows == ["TEST"]  # RULE nuốt cả UPDATE lẫn DELETE


def test_nhat_ky_ghi_duoc_khi_chua_co_vong(db, actor):
    """Tạo lệnh / Submit / huỷ xảy ra TRƯỚC khi có lượt nào — round_id phải rỗng được."""
    mo = _mo(db, actor, code="M131313")
    db.execute(
        text("INSERT INTO mo_event (mo_id, action, round_id) VALUES (:m, 'MO_CREATE', NULL)"),
        {"m": mo.id},
    )
