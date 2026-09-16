"""`mo_event.action` là sổ vĩnh viễn — canh nó không trôi.

Khác `error_codes.py` ở một điểm quyết định: mã lỗi gõ sai thì FE hiện nhầm màn
hình một lần rồi thôi, còn `action` gõ sai thì nằm lại `mo_event` VĨNH VIỄN —
RULE ở CSDL chặn UPDATE và DELETE, không ai sửa được nữa.

Cột dưới CSDL là `text` trần, không CHECK. Nên `action_codes.py` cộng file này là
lớp canh DUY NHẤT.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from sqlalchemy import text

from app.common.event_log import repository as event_repo
from app.common.vocab.action_codes import Act, step_accept

APP = Path(__file__).resolve().parents[1] / "app"
NGUON = [p for p in APP.rglob("*.py")
         if "__pycache__" not in p.parts and "migrations" not in p.parts
         and p.name != "action_codes.py"]


def test_khong_con_chuoi_action_tran():
    """Mọi `action=` phải trỏ vào `Act`, không phải chuỗi gõ tay hay f-string."""
    pham = []
    for tep in NGUON:
        for i, d in enumerate(tep.read_text(encoding="utf-8").splitlines(), 1):
            if re.search(r'action ?= ?f?"', d):
                pham.append(f"  {tep.relative_to(APP)}:{i}  {d.strip()[:70]}")
    assert not pham, "\nDùng Act.<TÊN> thay vì chuỗi trần:\n" + "\n".join(pham)


def test_gia_tri_bang_dung_ten():
    """`Act.RUN_START` phải ghi xuống sổ đúng chuỗi `"RUN_START"`."""
    lech = [f"{m.name} = {m.value!r}" for m in Act if m.value != m.name]
    assert not lech, "Giá trị lệch tên: " + ", ".join(lech)


def test_hanh_dong_nao_cung_co_noi_phat():
    """Khai một hành động rồi không phát = vốn từ chết, đọc sổ tưởng có mà không có."""
    dung = set()
    for tep in NGUON:
        nguon = tep.read_text(encoding="utf-8")
        dung |= set(re.findall(r"\bAct\.([A-Z_0-9]+)", nguon))
        if "step_accept(" in nguon:
            dung |= {f"STEP{n}_ACCEPT" for n in range(6)}
    thua = sorted({m.name for m in Act} - dung)
    assert not thua, "Khai mà không nơi nào phát: " + ", ".join(thua)


def test_step_accept_chan_tram_la():
    """Ghép chuỗi `f"STEP{n}_ACCEPT"` thì trạm 9 vẫn ghi xuống sổ ngon lành."""
    assert step_accept(0) is Act.STEP0_ACCEPT
    assert step_accept(5) is Act.STEP5_ACCEPT
    for lac in (-1, 6, 9):
        with pytest.raises(ValueError, match="chỉ có trạm 0 đến 5"):
            step_accept(lac)


def test_ghi_xuong_CSDL_ra_chuoi_tran(db, make_mo, flow):
    """`StrEnum` phải xuống cột `text` thành `"MO_SUBMIT"`, không phải `"Act.MO_SUBMIT"`."""
    code = make_mo()
    flow.accept(code, 0)
    db.flush()   # đẩy hàng xuống để đọc lại bằng SQL thô

    hanh_dong = set(db.scalars(text(
        "SELECT DISTINCT action FROM mo_event WHERE action LIKE 'MO%' OR action LIKE 'STEP%'"
    )))
    assert "MO_SUBMIT" in hanh_dong
    assert "STEP0_ACCEPT" in hanh_dong
    assert not any(a.startswith("Act.") for a in hanh_dong), f"lọt tên enum: {hanh_dong}"


def test_log_nhan_Act_va_chuoi_tuong_duong():
    """`Act` là `StrEnum` nên so với chuỗi thường vẫn đúng — đừng phá tính chất đó."""
    assert Act.MO_SUBMIT == "MO_SUBMIT"
    assert event_repo.log.__doc__ and "Act" in event_repo.log.__doc__
