"""Ranh giới giao dịch nằm ở service — kiểm đúng hai lời hứa của nó.

1. Gọi service xong là **dữ liệu đã nằm trong CSDL** (không ai quên commit).
2. Hỏng giữa chừng thì **không còn dấu vết gì** — kể cả khi một service gọi
   service khác (propagation REQUIRED).

Lời hứa 1 phải kiểm bằng session SẠCH: fixture `db` chung bọc sẵn mỗi test trong
một giao dịch rồi rollback, nên nó không phân biệt được "đã commit" với "chưa".
"""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from app.common.errors import DomainError
from app.common.uow import transaction
from app.modules.auth.models import AppUser
from app.modules.mo import service as mo_service
from app.modules.warehouse_out import service as warehouse_out_service


@pytest.fixture
def phien_sach(engine):
    """Session độc lập, giống hệt `SessionLocal` lúc chạy thật — KHÔNG bọc giao dịch."""
    tao = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    s = tao()
    try:
        yield s
    finally:
        s.rollback()
        s.close()


@pytest.fixture
def nguoi(phien_sach):
    """Tài khoản mới mỗi lần chạy, KHÔNG dọn sau khi xong.

    Dọn không được, mà cũng không nên: MO đã tạo trỏ về người tạo, và §25A cấm
    xoá nhật ký nên MO cũng không xoá được. Mã ngẫu nhiên là đủ để không đụng
    nhau giữa các lần chạy.
    """
    u = AppUser(full_name="Kiểm UOW", emp_code=f"T-UOW-{uuid.uuid4().hex[:8]}",
                roles=["PLANNER"])
    phien_sach.add(u)
    phien_sach.commit()
    return u.id


def test_goi_service_xong_la_DA_COMMIT(phien_sach, engine, nguoi):
    """Không có `with db.begin()` ở router nữa — phải chắc service tự commit.

    Kiểm bằng một KẾT NỐI KHÁC: dữ liệu chỉ thấy được từ bên ngoài khi đã commit
    thật, chứ không phải còn nằm trong session.
    """
    code = f"M9{uuid.uuid4().int % 100000:05d}"
    mo_service.create(phien_sach, [mo_service.NewMo(code, "Vỏ nhựa", 10, 600)], nguoi)

    with engine.connect() as ket_noi_khac:
        thay = ket_noi_khac.execute(
            text("SELECT count(*) FROM manufacturing_order WHERE code = :c"), {"c": code}
        ).scalar()
    assert thay == 1, "service không commit — dữ liệu không ra khỏi session"


def test_service_nem_loi_thi_KHONG_GHI_GI(phien_sach, engine, nguoi):
    """Mã thứ hai trùng mã thứ nhất → cả lô phải hỏng, không mã nào vào CSDL."""
    code = f"M9{uuid.uuid4().int % 100000:05d}"
    items = [mo_service.NewMo(code, "Vỏ nhựa", 10, 600),
             mo_service.NewMo(code, "Vỏ nhựa", 10, 600)]   # trùng — UNIQUE chặn
    with pytest.raises(IntegrityError):
        mo_service.create(phien_sach, items, nguoi)
    phien_sach.rollback()

    with engine.connect() as ket_noi_khac:
        thay = ket_noi_khac.execute(
            text("SELECT count(*) FROM manufacturing_order WHERE code = :c"), {"c": code}
        ).scalar()
    assert thay == 0, "lỗi giữa chừng mà vẫn ghi được — giao dịch không bọc kín"


# ── Propagation REQUIRED ────────────────────────────────────────────────────


def test_ca_lo_hong_thi_KHONG_MA_NAO_duoc_ban_giao(db, make_mo, flow, actor):
    """§7A: "một mã hỏng thì cả lô không lệnh nào được bàn giao".

    `handover_batch` mở giao dịch, `handover` bên trong NHẬP VÀO chứ không mở
    cái mới. Không có propagation thì hai mã đầu đã giao xong rồi mới tới mã hỏng.
    """
    a, b, c = make_mo(), make_mo(), make_mo()
    flow.accept(a, 0)
    flow.accept(b, 0)
    # c CHƯA quét nhận ở trạm 0 → handover sẽ ném

    with pytest.raises(DomainError):
        warehouse_out_service.handover_batch(db, codes=[a, b, c], actor_id=actor)

    con_lai = db.execute(text("SELECT count(*) FROM warehouse_out")).scalar()
    assert con_lai == 0, "mã hỏng ở cuối lô mà hai mã đầu vẫn được giao"


def test_lo_sach_thi_giao_het(db, make_mo, flow, actor):
    a, b = make_mo(), make_mo()
    flow.accept(a, 0)
    flow.accept(b, 0)
    assert warehouse_out_service.handover_batch(db, codes=[a, b], actor_id=actor) == 2
    assert db.execute(text("SELECT count(*) FROM warehouse_out")).scalar() == 2


def test_goi_long_nhau_KHONG_mo_giao_dich_moi(db, make_mo, flow, actor):
    """Bằng chứng trực tiếp của REQUIRED: gọi service trong một `transaction()`
    đang mở thì nó dùng chung, nên rollback ở ngoài xoá sạch được việc bên trong."""
    a = make_mo()
    flow.accept(a, 0)

    with pytest.raises(RuntimeError):
        with transaction(db):
            warehouse_out_service.handover(db, code=a, actor_id=actor)
            raise RuntimeError("đổi ý giữa chừng")

    assert db.execute(text("SELECT count(*) FROM warehouse_out")).scalar() == 0
