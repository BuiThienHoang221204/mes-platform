"""Dò lại số dòng cho mọi link trong `docs/` và ghi đè link cho đúng.

Tài liệu trong `docs/` trỏ vào mã nguồn bằng link kèm khoảng dòng:

    [`qc/service.py:34-66`](../mes-backend/app/modules/qc/service.py#L34-L66)
    <!--at: def qc_decide-->        ← thực tế nằm liền sau dấu `)`, tách dòng cho vừa khổ

Số dòng lệch ngay khi ai đó thêm một dòng phía trên. Nên thứ giữ link đúng không
phải con số, mà cái **neo** `<!--at: …-->` đứng sau nó — chú thích HTML, không hiện
khi xem tài liệu. Script này đọc neo, dò lại vị trí thật, rồi viết lại con số.

Bốn dạng neo:

    <!--at: def ten_ham-->          hàm/lớp — tự gộp cả `@decorator` phía trên
    <!--at: dòng đầu -> dòng cuối-->  khớp theo đầu dòng, hai mốc
    <!--at: dòng đầu +N-->          từ dòng đầu, lấy thêm N dòng
    <!--at: FILE-->                 cả file

Đổi tên hàm thì neo không dò được và script báo lỗi — đúng lúc cần biết.

    python tools/docs_link.py          sửa link
    python tools/docs_link.py --check  chỉ kiểm, lệch thì thoát mã 1 (dùng cho CI)
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

_out = getattr(sys.stdout, "reconfigure", None)
if _out is not None:
    _out(encoding="utf-8", errors="replace")


GOC = Path(__file__).resolve().parents[2]          # thư mục dự án
BE = GOC / "mes-backend"
DOCS = GOC / "docs"

LINK = re.compile(
    r"\[`(?P<nhan>[^`]+)`\]\((?P<duong>\.\./mes-backend/(?P<rel>[^)#]+))"
    r"#L(?P<d1>\d+)(?:-L(?P<d2>\d+))?\)<!--at:\s*(?P<neo>.+?)-->"
)


class KhongDoDuoc(Exception):
    """Neo không khớp dòng nào — thường là vì hàm đã đổi tên hoặc bị xoá."""


def _tim_dau_dong(dong: list[str], moc: str, tu: int = 0) -> int:
    """Chỉ số dòng đầu tiên (từ `tu` trở đi) có nội dung bắt đầu bằng `moc`."""
    for i in range(tu, len(dong)):
        if dong[i].strip().startswith(moc.strip()):
            return i
    raise KhongDoDuoc(moc)


def _het_khoi(dong: list[str], dau: int) -> int:
    """Dòng cuối của một khối Python bắt đầu ở `dau` — theo mức thụt đầu dòng."""
    muc = len(dong[dau]) - len(dong[dau].lstrip())
    cuoi = dau
    for i in range(dau + 1, len(dong)):
        if not dong[i].strip():
            continue
        if len(dong[i]) - len(dong[i].lstrip()) <= muc:
            break
        cuoi = i
    return cuoi


def giai_neo(dong: list[str], neo: str) -> tuple[int, int]:
    """Neo → (dòng đầu, dòng cuối), đánh số từ 1."""
    if neo == "FILE":
        return 1, len(dong)

    if neo.startswith(("def ", "class ")):
        dau = _tim_dau_dong(dong, neo)
        while dau > 0 and dong[dau - 1].strip().startswith("@"):
            dau -= 1                               # gộp cả decorator
        return dau + 1, _het_khoi(dong, _tim_dau_dong(dong, neo)) + 1

    if " -> " in neo:
        a, b = neo.split(" -> ", 1)
        dau = _tim_dau_dong(dong, a)
        return dau + 1, _tim_dau_dong(dong, b, dau) + 1

    m = re.fullmatch(r"(.+?) \+(\d+)", neo)
    if m:
        dau = _tim_dau_dong(dong, m.group(1))
        return dau + 1, dau + 1 + int(m.group(2))

    dau = _tim_dau_dong(dong, neo)
    return dau + 1, dau + 1


def xu_ly(tep: Path, chi_kiem: bool) -> list[str]:
    noi_dung = tep.read_text(encoding="utf-8")
    lech: list[str] = []

    def thay(m: re.Match[str]) -> str:
        rel, neo = m["rel"], m["neo"]
        nguon = BE / rel
        if not nguon.is_file():
            lech.append(f"{tep.name}: không có tệp {rel}")
            return m.group(0)
        try:
            d1, d2 = giai_neo(nguon.read_text(encoding="utf-8").splitlines(), neo)
        except KhongDoDuoc as e:
            lech.append(f"{tep.name}: neo không dò được trong {rel} — <!--at: {e}-->")
            return m.group(0)

        cu = (int(m["d1"]), int(m["d2"] or m["d1"]))
        if cu != (d1, d2):
            lech.append(f"{tep.name}: {rel} {cu[0]}-{cu[1]} → {d1}-{d2}")

        ten = rel.split("/")[-1]
        thu_muc = rel.split("/")[-2] if "/" in rel else ""
        nhan = f"{thu_muc}/{ten}" if thu_muc not in ("", "versions") else ten
        so = f"{d1}-{d2}" if d2 > d1 else str(d1)
        khoang = f"L{d1}-L{d2}" if d2 > d1 else f"L{d1}"
        return f"[`{nhan}:{so}`]({m['duong']}#{khoang})<!--at: {neo}-->"

    moi = LINK.sub(thay, noi_dung)
    if not chi_kiem and moi != noi_dung:
        tep.write_text(moi, encoding="utf-8", newline="\n")
    return lech


def main() -> int:
    chi_kiem = "--check" in sys.argv
    tat_ca: list[str] = []
    so_link = 0
    for tep in sorted(DOCS.glob("*.md")):
        so_link += len(LINK.findall(tep.read_text(encoding="utf-8")))
        tat_ca += xu_ly(tep, chi_kiem)

    print(f"Link có neo: {so_link}")
    if not tat_ca:
        print("Mọi link đã đúng số dòng.")
        return 0
    print("Lệch — đã sửa:" if not chi_kiem else "Lệch:")
    for d in tat_ca:
        print("   " + d)
    return 1 if chi_kiem else 0


if __name__ == "__main__":
    raise SystemExit(main())
