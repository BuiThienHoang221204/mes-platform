"""`tools/seed_demo.py` phải gọi được tầng service — nó mục thầm rất dễ.

Seeder không nằm trong đường đi của ứng dụng nên không ai chạy nó khi sửa service.
Đổi chữ ký một hàm là nó gãy, mà chỉ lộ ra lúc có người ngồi nạp dữ liệu — lần gần
nhất là giữa chừng một lượt nạp lên máy chủ thật, sau khi đã ghi được nửa lô.

Test này đi trọn MỘT vòng: tạo → chốt lệnh → qua sáu bước → chia chuyền → ghi sổ giờ
→ chốt sổ → đóng thùng → nhập kho. Đủ chạm mọi service mà seeder dùng.
"""

from __future__ import annotations

import random
import sys
from pathlib import Path

import pytest
from sqlalchemy import text

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))


@pytest.fixture
def seeder(db):
    import seed_demo

    for emp in ("NV001", "NV010", "NV020", "NV030", "NV040", "NV050", "NV060", "NV070"):
        if not db.execute(
            text("SELECT 1 FROM app_user WHERE emp_code = :e"), {"e": emp}
        ).first():
            pytest.skip(f"CSDL test chưa có tài khoản {emp}")

    return seed_demo.Seeder(db, random.Random(1))


def test_mot_vong_tron_chay_duoc(seeder, db):
    code, _, box = seeder.new_mo()
    seeder.submit(code)
    seeder.ready_for(code, 4)
    seeder.accept(code, 4, "NV050")
    seeder.full_round(code, "L01", box, days=2)

    status = db.execute(
        text("SELECT status FROM manufacturing_order WHERE code = :c"), {"c": code}
    ).scalar()
    assert status is not None


def test_ghi_so_gio_LUON_co_dong_cua_hom_nay(seeder, db):
    """Màn báo cáo mặc định xem hôm nay — không có dòng nào của hôm nay thì nó trắng."""
    from datetime import date

    code, qty, _ = seeder.new_mo()
    seeder.submit(code)
    seeder.ready_for(code, 4)
    seeder.accept(code, 4, "NV050")
    seeder.assign(code, "L02")
    seeder.start(code, "L02")
    seeder.hourly(code, qty, days=3, fill=0.8)

    n = db.execute(
        text("SELECT count(*) FROM hourly_output h"
             " JOIN mo_round r ON r.id = h.round_id"
             " JOIN manufacturing_order m ON m.id = r.mo_id"
             " WHERE m.code = :c AND h.work_date = :d"),
        {"c": code, "d": date.today()},
    ).scalar()
    assert n and n > 0, "không có dòng sản lượng giờ nào của hôm nay"


def test_dong_thung_theo_gio_co_dong_cua_hom_nay(seeder, db):
    from datetime import date

    code, qty, box = seeder.new_mo()
    while not box:
        code, qty, box = seeder.new_mo()
    seeder.submit(code)
    seeder.ready_for(code, 4)
    seeder.accept(code, 4, "NV050")
    seeder.assign(code, "L03")
    seeder.start(code, "L03")
    made = seeder.hourly(code, qty, days=1, fill=0.9)
    ok = seeder.close_book(code, qty, made)
    seeder.pack_boxes(code, box, ok, days=2)

    n = db.execute(
        text("SELECT count(*) FROM packing_hourly p"
             " JOIN mo_round r ON r.id = p.round_id"
             " JOIN manufacturing_order m ON m.id = r.mo_id"
             " WHERE m.code = :c AND p.work_date = :d"),
        {"c": code, "d": date.today()},
    ).scalar()
    assert n and n > 0, "không có dòng đóng thùng nào của hôm nay"


def test_vong_2_mo_duoc_sau_khi_thieu_so(seeder, db):
    code, _, box = seeder.new_mo()
    seeder.submit(code)
    seeder.ready_for(code, 4)
    seeder.accept(code, 4, "NV050")
    seeder.part_round(code, "L04", box, fill=0.4)

    rounds = db.execute(
        text("SELECT count(*) FROM mo_round r"
             " JOIN manufacturing_order m ON m.id = r.mo_id WHERE m.code = :c"),
        {"c": code},
    ).scalar()
    assert rounds == 2, f"thiếu số mà không mở vòng 2 (có {rounds} vòng)"
