"""Canh ranh giới giữa các tầng — thứ mà `ruff` và test nghiệp vụ đều không thấy.

Luật của dự án (BE-PLAN §"SQL chỉ được nằm trong repository.py"):

    router    HTTP thôi — kiểm quyền, gọi service, dựng câu trả lời
    service   luật nghiệp vụ + ranh giới giao dịch
    repository MỌI câu truy vấn và MỌI lời ghi xuống CSDL

Vi phạm luật này không làm test nào đỏ, không làm `ruff` kêu. Nó chỉ làm code khó
lần khi có sự cố: "bảng này bị đụng ở đâu" phải đi tìm khắp nơi thay vì mở một file.

Test ở đây đọc MÃ NGUỒN, không chạy CSDL.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

APP = Path(__file__).resolve().parents[1] / "app"

SERVICE = sorted(APP.glob("modules/*/service.py")) + sorted(APP.glob("modules/*/*_service.py"))
ROUTER = sorted(APP.glob("modules/*/router.py"))


def _dong_code(tep: Path) -> list[tuple[int, str]]:
    """Bỏ dòng trống, chú thích và docstring — chỉ giữ dòng có mã thật."""
    ra, trong_docstring = [], False
    for i, d in enumerate(tep.read_text(encoding="utf-8").splitlines(), 1):
        nhay = d.count('"""')
        if trong_docstring:
            trong_docstring = nhay % 2 == 0
            continue
        if nhay:
            trong_docstring = nhay % 2 == 1
            continue
        if d.strip() and not d.strip().startswith("#"):
            ra.append((i, d))
    return ra


@pytest.mark.parametrize("tep", SERVICE, ids=lambda p: f"{p.parent.name}/{p.name}")
def test_service_KHONG_tu_viet_truy_van(tep: Path):
    """Service không được viết SQL hay dựng truy vấn — việc đó của repository.

    Cho phép `db.flush()`: nó không ghi thêm gì, chỉ đẩy thay đổi đang treo xuống
    sớm để lỗi ràng buộc nổ đúng dòng (xem `qc_decide`).
    """
    cam = {
        r"\btext\(": "SQL thô — chuyển sang repository",
        r"\bselect\(": "dựng truy vấn — chuyển sang repository",
        r"db\.execute\(": "chạy câu lệnh — chuyển sang repository",
        r"db\.add\(": "ghi dòng mới — dùng repo.save_*()",
        r"db\.scalar[s]?\(": "đọc thẳng — chuyển sang repository",
        r"db\.get\(": "đọc thẳng — chuyển sang repository",
    }
    pham = [f"  dòng {i}: {vi}\n      {d.strip()[:70]}"
            for i, d in _dong_code(tep)
            for mau, vi in cam.items() if re.search(mau, d)]
    assert not pham, f"\n{tep.name} chạm thẳng CSDL:\n" + "\n".join(pham)


@pytest.mark.parametrize("tep", ROUTER, ids=lambda p: p.parent.name)
def test_router_KHONG_cham_CSDL(tep: Path):
    """Router chỉ được: kiểm quyền → gọi service → dựng câu trả lời.

    Ngoại lệ có chủ ý là các endpoint CHỈ ĐỌC — không có luật nghiệp vụ nào để
    service phải lo, nên chúng gọi thẳng `repo.get_*` / `repo.list_*`:
    `GET /mos/{code}` ở `mo/`, và hai endpoint danh mục ở `catalog/`.

    Ngoại lệ đó chỉ nới cho hàm ĐỌC. Từ lúc `catalog/` có POST và DELETE, hai
    đường ghi ấy vẫn phải đi qua service — nếu không thì không ai commit
    (`get_db` không quản giao dịch) và câu INSERT biến mất lặng lẽ.
    """
    if tep.parent.name == "mo":
        pytest.skip("mo/ — GET /mos/{code} đọc thẳng repository, có chủ ý")

    doc_thang = re.compile(r"_repo\.(get|list)_")
    pham = [f"  dòng {i}: {d.strip()[:70]}"
            for i, d in _dong_code(tep)
            if re.search(r"\btext\(|\bselect\(|db\.(execute|add|scalars?|get|flush)\(|_repo\.", d)
            and not (tep.parent.name == "catalog" and doc_thang.search(d))]
    assert not pham, f"\n{tep.name} chạm CSDL:\n" + "\n".join(pham)


def test_gio_ghi_vao_CSDL_phai_lay_TU_CSDL():
    """Nguyên tắc ③ — mốc `_at` do CSDL sinh, không lấy đồng hồ máy ứng dụng.

    Đồng hồ các máy lệch nhau thì `submitted_at` không so được với
    `mo_step.opened_at`, mà cả hệ này sống bằng cách trừ hai mốc thời gian.
    `common/clock.py` là chỗ DUY NHẤT được viết hai câu lấy giờ đó.
    """
    pham = []
    for tep in APP.rglob("*.py"):
        if tep.name in ("clock.py", "__init__.py") or "migrations" in tep.parts:
            continue
        for i, d in _dong_code(tep):
            if re.search(r'text\("SELECT (now|clock_timestamp)\(\)"\)', d):
                pham.append(f"  {tep.relative_to(APP)}:{i} — dùng clock.db_now/db_clock")
    assert not pham, "\nLấy giờ CSDL ngoài clock.py:\n" + "\n".join(pham)
