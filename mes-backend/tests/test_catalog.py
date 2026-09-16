"""Quản trị danh mục chuyền — thêm và xoá.

Ba điều đáng canh, vì cả ba đều là thứ CSDL quyết định chứ không phải Python:

    1. `line.id` không tự tăng — repository phải tự cấp số, cấp sai là đụng khoá chính.
    2. Mã chuyền UNIQUE, mà `l15` với `L15` là hai chuỗi khác nhau — service chuẩn hoá.
    3. Khoá ngoại `line_segment` chặn xoá chuyền đã chạy, và câu lỗi phải ra tiếng Việt.
"""

from __future__ import annotations

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.common.errors import NotFound, translate_db_error
from app.common.vocab.error_codes import Err
from app.modules.catalog import repository as catalog_repo
from app.modules.catalog import service as catalog_service


def test_them_chuyen_duoc_cap_id_ke_tiep(db):
    cao_nhat = max(line.id for line in catalog_repo.list_lines(db))

    moi = catalog_service.create_line(db, code="L90", name="Chuyền thử")

    assert moi.id == cao_nhat + 1, "id phải nối tiếp — cột này không tự tăng"

    # Đọc lại bằng SQL: chứng minh `@transactional` có mở ranh giới và ĐÃ đẩy câu
    # INSERT xuống. Thiếu nó thì hàng chỉ nằm trong bộ nhớ session rồi mất.
    assert db.scalar(text("SELECT name FROM line WHERE code = 'L90'")) == "Chuyền thử"


def test_ma_chuyen_chuan_hoa_ve_chu_hoa(db):
    """`l91` và `L91` phải là MỘT chuyền, không phải hai."""
    catalog_service.create_line(db, code="  l91  ")

    assert catalog_repo.get_line(db, "L91") is not None

    with pytest.raises(IntegrityError) as e:
        catalog_service.create_line(db, code="L91")

    loi = translate_db_error(e.value)
    assert loi is not None and loi.code == Err.LINE_DUPLICATE


def test_xoa_chuyen_chua_ai_dung(db):
    catalog_service.create_line(db, code="L92")

    catalog_service.delete_line(db, "l92")

    with pytest.raises(NotFound):
        catalog_repo.get_line(db, "L92")


def test_xoa_chuyen_da_chay_bi_chan(db, make_mo, flow):
    """Chuyền đã có lịch sử thì khoá ngoại chặn — và người dùng phải đọc được vì sao."""
    code = make_mo(qty=100, minutes=30)
    flow.accept(code, 0)
    flow.handover(code)
    flow.accept(code, 1)
    flow.accept(code, 2)
    flow.qc(code, "PASS")
    flow.accept(code, 3)
    flow.accept(code, 4)
    flow.run_line(code, "L01")

    with pytest.raises(IntegrityError) as e:
        catalog_service.delete_line(db, "L01")

    loi = translate_db_error(e.value)
    assert loi is not None
    assert loi.code == Err.LINE_IN_USE
    assert loi.status == 409
    assert "TẮT" in loi.message, "phải chỉ đường: tắt chuyền thay vì xoá"
