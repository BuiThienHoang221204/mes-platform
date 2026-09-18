"""Backend không tin gì từ client — mọi biên phải nằm ở đây, không ở form.

Các ô SỐ đã được chặn bằng `gt=0`/`ge=0` từ đầu. Nhưng mọi cột chữ trong CSDL đều
là `Text` (không có trần) và schema cũng khai `str` trần, nghĩa là biên duy nhất
đang nằm ở form của trình duyệt — mà form thì ai cũng bỏ qua được bằng `curl`.

Không cần ác ý mới chạm tới: một máy quét mã vạch kẹt phím cũng đủ đẩy vài trăm
nghìn ký tự vào `product_name`.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.modules.auth.schemas import LoginIn
from app.modules.mo.schemas import MoCancelIn, MoCreateIn
from app.modules.packing.schemas import PackingFinishIn, PackingHourlyIn
from app.modules.production.schemas import HourlyIn, LineHoldIn, ProductionCloseIn
from app.modules.qc.schemas import QcDecideIn


def _mo(**kw):
    return MoCreateIn(**{"code": "M100200", "product_name": "Vỏ hộp số",
                         "quantity": 1000, "required_production_min": 60, **kw})


# ══ Chuỗi phải có trần ═══════════════════════════════════════════════════════
def test_ten_con_hang_khong_duoc_dai_vo_han():
    with pytest.raises(ValidationError):
        _mo(product_name="X" * 201)


def test_ten_con_hang_toan_dau_cach_bi_chan():
    """`min_length=1` một mình là vô dụng: "   " dài 3 nên lọt, và ta lưu tên rỗng."""
    with pytest.raises(ValidationError):
        _mo(product_name="   ")


def test_ten_con_hang_duoc_cat_dau_cach_thua():
    assert _mo(product_name="  Niềng xe  ").product_name == "Niềng xe"


@pytest.mark.parametrize(
    "dung",
    [
        lambda t: QcDecideIn(result="FAIL", reason_text=t),
        lambda t: LineHoldIn(line_code="L01", reason_text=t),
        lambda t: ProductionCloseIn(qty_ok=1, qty_ng=0, qty_short=0, ng_reason_text=t),
        lambda t: MoCancelIn(reason=t),
    ],
)
def test_moi_o_ly_do_deu_co_tran(dung):
    with pytest.raises(ValidationError):
        dung("X" * 501)


def test_ly_do_huy_toan_dau_cach_bi_chan():
    """§4A bắt buộc ghi lý do huỷ. Dấu cách không phải lý do."""
    with pytest.raises(ValidationError):
        MoCancelIn(reason="    ")


def test_ghi_chu_duoc_phep_rong_nhung_van_co_tran():
    assert PackingFinishIn(qty_packed=10, note_text="").note_text == ""
    with pytest.raises(ValidationError):
        PackingFinishIn(qty_packed=10, note_text="X" * 501)


# ══ Đăng nhập: chặn thân request khổng lồ trước khi đụng tới băm ════════════
def test_ma_pin_va_ma_nhan_vien_co_tran():
    with pytest.raises(ValidationError):
        LoginIn(emp_code="N" * 33, pin="1234")
    with pytest.raises(ValidationError):
        LoginIn(emp_code="NV001", pin="9" * 65)


def test_ma_pin_khong_bi_ep_bo_ky_tu():
    """Chỉ chặn độ dài. Siết charset là khoá cửa tài khoản dùng quy ước khác."""
    assert LoginIn(emp_code="NV001", pin="a1-b2").pin == "a1-b2"


# ══ Số âm: đã chặn sẵn, khoá lại để không ai nới ═══════════════════════════
@pytest.mark.parametrize(
    "dung",
    [
        lambda: _mo(quantity=-1),
        lambda: _mo(required_production_min=-1),
        lambda: _mo(pcs_per_box=-1),
        lambda: ProductionCloseIn(qty_ok=-1, qty_ng=0, qty_short=0),
        lambda: ProductionCloseIn(qty_ok=0, qty_ng=-1, qty_short=0),
        lambda: ProductionCloseIn(qty_ok=0, qty_ng=0, qty_short=-1),
        lambda: HourlyIn(work_date="2026-09-16", slot_hour=8, headcount=-1, target_qty=1, qty=1),
        lambda: HourlyIn(work_date="2026-09-16", slot_hour=-1, headcount=1, target_qty=1, qty=1),
        lambda: HourlyIn(work_date="2026-09-16", slot_hour=24, headcount=1, target_qty=1, qty=1),
        lambda: PackingHourlyIn(work_date="2026-09-16", slot_hour=8, boxes=-1),
        lambda: PackingHourlyIn(work_date="2026-09-16", slot_hour=8, boxes=0),
        lambda: PackingFinishIn(qty_packed=0),
    ],
)
def test_so_am_va_so_khong_hop_le_bi_chan(dung):
    with pytest.raises(ValidationError):
        dung()
