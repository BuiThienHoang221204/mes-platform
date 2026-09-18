"""Kiểm mọi thứ bấm được trong `docs/` có dẫn tới đâu đó có thật.

Ba thứ được kiểm:

1. **Link vào mã nguồn** — tệp có tồn tại, khoảng dòng nằm trong tệp, và nếu link
   có neo `<!--at: …-->` thì dòng đầu phải khớp neo. Bấm vào mà nhảy sai chỗ thì
   tài liệu còn tệ hơn không có link.
2. **Link sang tài liệu khác** — tệp có tồn tại.
3. **Neo trong trang** (`[x](#muc-3)`) — có `<a id="…">` tương ứng.

Không sửa gì, chỉ báo. Lệch thì thoát mã 1 — chạy được trong CI.

    python tools/docs_check.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

_out = getattr(sys.stdout, "reconfigure", None)
if _out is not None:
    _out(encoding="utf-8", errors="replace")


GOC = Path(__file__).resolve().parents[2]
BE = GOC / "mes-backend"
DOCS = GOC / "docs"

LINK_CODE = re.compile(
    r"\]\(\.\./mes-backend/(?P<rel>[^)#]+)#L(?P<d1>\d+)(?:-L(?P<d2>\d+))?\)"
    r"(?:<!--at:\s*(?P<neo>.+?)-->)?"
)
LINK_TEP = re.compile(r"\]\((?!https?:|#)(?P<duong>[^)#]+\.md)\)")
LINK_NEO = re.compile(r"\]\(#(?P<neo>[^)]+)\)")
THE_NEO = re.compile(r'<a id="(?P<id>[^"]+)">')


def kiem(tep: Path) -> list[str]:
    s = tep.read_text(encoding="utf-8")
    loi: list[str] = []

    # 1. link vào mã nguồn
    for m in LINK_CODE.finditer(s):
        nguon = BE / m["rel"]
        if not nguon.is_file():
            loi.append(f"không có tệp: {m['rel']}")
            continue
        dong = nguon.read_text(encoding="utf-8").splitlines()
        d1, d2 = int(m["d1"]), int(m["d2"] or m["d1"])
        if d2 > len(dong):
            loi.append(f"{m['rel']}: trỏ tới dòng {d2} nhưng tệp chỉ có {len(dong)}")
            continue
        neo = m["neo"]
        if not neo:
            loi.append(f"{m['rel']}:{d1} thiếu neo <!--at: …--> nên không dò lại được")
            continue
        if neo == "FILE":
            continue
        moc = re.sub(r" \+\d+$", "", neo.split(" -> ")[0]).strip()

        # Neo dạng `def …` trỏ tới hàm, mà `docs_link` cố ý gộp cả `@decorator`
        # phía trên — nên dòng đầu có thể là decorator. Chấp nhận nếu mốc nằm
        # trong khoảng và mọi dòng trước nó trong khoảng đều là decorator.
        if moc.startswith(("def ", "class ")):
            trong = [i for i in range(d1 - 1, d2) if dong[i].strip().startswith(moc)]
            if not trong:
                loi.append(f"{m['rel']}:{d1}-{d2} không chứa `{moc}`")
            elif any(not dong[i].strip().startswith("@") for i in range(d1 - 1, trong[0])):
                loi.append(f"{m['rel']}:{d1} bắt đầu trước `{moc}` mà không phải decorator")
            continue

        if not dong[d1 - 1].strip().startswith(moc):
            loi.append(
                f"{m['rel']}:{d1} không khớp neo\n"
                f"       neo  : {moc}\n"
                f"       dòng : {dong[d1 - 1].strip()[:70]}"
            )

    # 2. link sang tài liệu khác
    for m in LINK_TEP.finditer(s):
        if not (tep.parent / m["duong"]).resolve().is_file():
            loi.append(f"không có tài liệu: {m['duong']}")

    # 3. neo trong trang
    co = set(THE_NEO.findall(s))
    for m in LINK_NEO.finditer(s):
        if m["neo"] not in co:
            loi.append(f"neo không tồn tại trong trang: #{m['neo']}")

    return loi


def main() -> int:
    tong = 0
    for tep in sorted(DOCS.glob("*.md")):
        loi = kiem(tep)
        so = len(LINK_CODE.findall(tep.read_text(encoding="utf-8")))
        print(f"{tep.name:28s} {so:2d} link mã nguồn  "
              + ("OK" if not loi else f"{len(loi)} LỖI"))
        for d in loi:
            print("     - " + d)
        tong += len(loi)
    print()
    print("Tất cả link đều dẫn đúng chỗ." if tong == 0 else f"{tong} link hỏng.")
    return 0 if tong == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
