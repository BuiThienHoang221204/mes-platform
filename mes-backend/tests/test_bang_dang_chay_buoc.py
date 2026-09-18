"""Bảng đang chạy phải nói được lệnh đang ở bước nào — BRD §9b.5.

Bảng cố ý hiện lệnh ở MỌI bước. Không có `current_step` thì lệnh vừa chốt trông
giống hệt lệnh đang lắp ráp dở, và màn hình mời nó đi chia chuyền.
"""

from __future__ import annotations

from app.modules.board import repository as board_repo


def _row(db, code: str) -> dict:
    return next(r for r in board_repo.running_rows(db, limit=100) if r["code"] == code)


def test_lenh_vua_chot_chua_buoc_nao_nhan(db, make_mo):
    code = make_mo(qty=1_000, minutes=60)
    assert _row(db, code)["current_step"] is None


def test_buoc_cao_nhat_da_nhan(db, make_mo, flow):
    code = make_mo(qty=1_000, minutes=60)
    flow.accept(code, 0)
    assert _row(db, code)["current_step"] == 0
    flow.handover(code)
    flow.accept(code, 1)
    assert _row(db, code)["current_step"] == 1
    flow.accept(code, 2)
    flow.qc(code, "PASS")
    flow.accept(code, 3)
    flow.accept(code, 4)
    assert _row(db, code)["current_step"] == 4


def test_chua_toi_san_xuat_thi_chua_chia_chuyen_duoc(db, make_mo, flow):
    """Cột `current_step` và luật của backend phải nói CÙNG một điều.

    Nút `Chia chuyền` ẩn khi `current_step < 4`. Nếu backend lại cho gán chuyền ở
    bước 1 thì màn hình giấu mất một thao tác hợp lệ — sai theo chiều ngược lại.
    """
    import pytest

    from app.common.errors import DomainError
    from app.common.vocab.error_codes import Err

    code = make_mo(qty=1_000, minutes=60)
    flow.accept(code, 0)
    flow.handover(code)
    flow.accept(code, 1)

    assert _row(db, code)["current_step"] < 4
    with pytest.raises(DomainError) as e:
        flow.assign_only(code, "L01")
    assert e.value.code == Err.NO_PRODUCTION_ACCEPT
