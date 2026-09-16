"""Mã lỗi là hợp đồng với frontend — canh nó không trôi.

FE nhìn `code` để quyết định hiện màn hình nào, không đọc `message` (câu tiếng Việt
sửa lúc nào cũng được). Nên hai chuyện phải giữ:

* **Không ai được gõ chuỗi trần.** Gõ sai một chữ thì FE nhận mã lạ mà backend không
  báo gì — chuỗi nào cũng hợp lệ. Qua `Err.X` thì gõ sai là `AttributeError` ngay.
* **Giá trị gửi ra phải đúng bằng TÊN mã.** Đổi giá trị là phá FE, y như đổi tên một
  endpoint.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from app.common.errors import DomainError, Forbidden, Invalid, NotFound
from app.common.vocab.error_codes import Err

APP = Path(__file__).resolve().parents[1] / "app"
NGUON = [p for p in APP.rglob("*.py")
         if "__pycache__" not in p.parts and "migrations" not in p.parts
         and p.name != "error_codes.py"]


def test_khong_con_chuoi_ma_loi_tran():
    """Mọi `code=` phải trỏ vào `Err`, không phải chuỗi gõ tay."""
    pham = []
    for tep in NGUON:
        for i, d in enumerate(tep.read_text(encoding="utf-8").splitlines(), 1):
            if re.search(r'code(?:: str)? ?= ?"[A-Z_0-9]+"', d):
                pham.append(f"  {tep.relative_to(APP)}:{i}  {d.strip()[:70]}")
    assert not pham, "\nDùng Err.<TÊN> thay vì chuỗi trần:\n" + "\n".join(pham)


def test_gia_tri_bang_dung_ten():
    """`Err.QC_DONE` phải gửi ra đúng chuỗi `"QC_DONE"`.

    Đặt giá trị khác tên thì đọc log thấy một đằng, tra code thấy một nẻo.
    """
    lech = [f"{m.name} = {m.value!r}" for m in Err if m.value != m.name]
    assert not lech, "Giá trị lệch tên: " + ", ".join(lech)


def test_ma_nao_cung_co_noi_dung():
    """Khai một mã rồi không dùng = rác, và FE có thể chờ một mã không bao giờ tới."""
    dung = set()
    for tep in NGUON:
        dung |= set(re.findall(r"\bErr\.([A-Z_0-9]+)", tep.read_text(encoding="utf-8")))
    thua = sorted({m.name for m in Err} - dung)
    assert not thua, "Mã khai mà không nơi nào dùng: " + ", ".join(thua)


def test_ma_di_ra_JSON_van_la_chuoi():
    """`StrEnum` phải serialize thành chuỗi trần, không phải `"Err.QC_DONE"`.

    `main.domain_error_handler` đưa thẳng `exc.code` vào `JSONResponse`.
    """
    e = DomainError("thử", code=Err.QC_DONE)
    assert json.dumps({"code": e.code}) == '{"code": "QC_DONE"}'
    assert e.code == "QC_DONE", "so sánh với chuỗi thường vẫn phải đúng"


def test_bon_lop_loi_giu_nguyen_ma_mac_dinh_va_ma_HTTP():
    """FE đang dựa vào bốn mã này — đổi là phá."""
    for lop, ma, http in [
        (DomainError, Err.DOMAIN, 409),
        (NotFound, Err.NOT_FOUND, 404),
        (Invalid, Err.INVALID, 422),
        (Forbidden, Err.FORBIDDEN, 403),
    ]:
        e = lop("thử")
        assert e.code == ma, f"{lop.__name__} đổi mã mặc định"
        assert e.status == http, f"{lop.__name__} đổi mã HTTP"
