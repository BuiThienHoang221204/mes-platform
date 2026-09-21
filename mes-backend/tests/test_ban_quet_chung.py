"""Bảng đang chạy và Tổng quan đọc CÙNG dữ liệu — phải dùng chung MỘT lượt quét.

Cắt trang từ lượt quét chung chỉ đúng khi nó cho ra y hệt `LIMIT/OFFSET` của SQL.
Ba ca dưới canh đúng điều đó, cộng với cái bẫy đi kèm: dict trong lượt quét dùng
chung, nên đổi giờ phải xảy ra ĐÚNG MỘT LẦN.

Xem `docs/RA-SOAT-POLLING.md` §5.1.
"""

from __future__ import annotations

import pytest
from sqlalchemy.orm import Session

from app.common import read_cache
from app.modules.board import repository as board_repo
from app.modules.board import service as board_service


@pytest.fixture
def open_orders(make_mo) -> list[str]:
    codes = [make_mo() for _ in range(8)]
    read_cache.clear()
    return sorted(codes)


@pytest.mark.parametrize("offset", [0, 2, 5, 7])
def test_cat_tu_ban_quet_chung_giong_het_phan_trang_bang_SQL(
    db: Session, open_orders: list[str], offset: int
):
    via_service = board_service.running_board(db, limit=3, offset=offset)
    via_sql = board_repo.running_rows(db, limit=3, offset=offset)

    assert [r["code"] for r in via_service["items"]] == [r["code"] for r in via_sql]
    assert via_service["total"] == len(open_orders)


def test_trang_vuot_qua_ban_quet_thi_hoi_thang_CSDL(
    db: Session, open_orders: list[str], monkeypatch
):
    monkeypatch.setattr(board_service, "OVERVIEW_SCAN", 4)
    read_cache.clear()

    within_scan = board_service.running_board(db, limit=2, offset=1)
    beyond_scan = board_service.running_board(db, limit=3, offset=5)

    assert [r["code"] for r in within_scan["items"]] == open_orders[1:3]
    assert [r["code"] for r in beyond_scan["items"]] == open_orders[5:8], (
        "trang nằm ngoài lượt quét chung phải rơi về đường SQL và vẫn đúng"
    )


def test_hai_man_hinh_dung_chung_MOT_luot_quet(db: Session, open_orders, monkeypatch):
    calls = {"n": 0}
    original = board_repo.running_rows

    def counting(*args, **kwargs):
        calls["n"] += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(board_repo, "running_rows", counting)

    board_service.running_board(db, limit=10, offset=0)
    board_service.overview(db)
    board_service.running_board(db, limit=10, offset=0)

    assert calls["n"] == 1, (
        f"quét {calls['n']} lượt cho cùng một tập dữ liệu — hai màn hình chưa dùng chung"
    )


def test_ghi_xong_thi_ban_quet_chung_phai_tuoi(db: Session, open_orders, make_mo):
    before = board_service.running_board(db, limit=10, offset=0)
    assert before["total"] == 8

    make_mo()

    after = board_service.running_board(db, limit=10, offset=0)
    assert after["total"] == 9, "lượt quét chung không được sống sót qua một lượt ghi"
    assert len(after["items"]) == 9


def test_doi_gio_chi_MOT_lan(db: Session, open_orders, flow):
    code = open_orders[0]
    flow.accept(code, 0)
    flow.handover(code)

    first_call = board_service.running_board(db, limit=10, offset=0)["items"]
    first_marks = {r["code"]: r["handed_over_at"] for r in first_call}

    second_call = board_service.running_board(db, limit=10, offset=0)["items"]
    second_marks = {r["code"]: r["handed_over_at"] for r in second_call}

    assert first_marks == second_marks, "gọi lần hai không được đổi giờ thêm một lần nữa"
