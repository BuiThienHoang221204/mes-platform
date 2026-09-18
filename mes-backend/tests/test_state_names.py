"""Nhãn `from_state` / `to_state` — chữ hiện thẳng lên màn hình Truy vết.

`board/service.py` trả hai cột này cho FE hiện nguyên văn, và `mo_event` không sửa
được (RULE ở CSDL chặn UPDATE/DELETE). Nên nhãn gõ lệch một chữ là lệch vĩnh viễn,
ngay trên bảng người vận hành đang nhìn.

Cái bẫy thật đã dính một lần: cùng trạm 0 mà chỗ ghi "Kho", chỗ ghi "Kho xuất";
trạm 5 thì "Nhập kho" với "Kho nhập". Ba bài dưới canh đúng lớp bẫy đó.
"""

from __future__ import annotations

import re
from pathlib import Path

from app.common.vocab.enums import STEP_NAMES, MoStatus
from app.common.vocab.state_names import State, round_label

APP = Path(__file__).resolve().parents[1] / "app"
NGUON = [p for p in APP.rglob("*.py")
         if "__pycache__" not in p.parts and "migrations" not in p.parts
         and p.name != "state_names.py"]


def test_khong_con_nhan_tran():
    """Mọi `from_state=` / `to_state=` phải trỏ vào `State`, `MoStatus` hoặc `STEP_NAMES`."""
    pham = []
    for tep in NGUON:
        for i, d in enumerate(tep.read_text(encoding="utf-8").splitlines(), 1):
            if re.search(r'(?:from|to)_state ?= ?f?"', d):
                pham.append(f"  {tep.relative_to(APP)}:{i}  {d.strip()[:70]}")
    assert not pham, "\nDùng State/MoStatus/STEP_NAMES thay vì chuỗi trần:\n" + "\n".join(pham)


def test_nhan_nao_cung_co_noi_dung():
    """Khai một nhãn rồi không ghi ra = chữ chết, đọc sổ tưởng có mà không có."""
    dung = set()
    for tep in NGUON:
        dung |= set(re.findall(r"\bState\.([A-Z_0-9]+)", tep.read_text(encoding="utf-8")))
    thua = sorted({m.name for m in State} - dung)
    assert not thua, "Khai mà không nơi nào ghi: " + ", ".join(thua)


def test_khong_hai_nhan_cung_mot_chu():
    """Hai nhãn trùng chữ thì trên màn hình không phân biệt được — mà chúng khác nghĩa."""
    chu = [m.value for m in State]
    trung = {c for c in chu if chu.count(c) > 1}
    assert not trung, "Nhãn trùng nhau: " + ", ".join(sorted(trung))


def test_nhan_KHONG_dam_vao_ten_tram():
    """Đây là lỗi đã từng có: cùng một trạm, hai lối viết, cùng hiện trên một bảng.

    Tên trạm là của `STEP_NAMES`. `State` chỉ giữ phần KHÔNG phải tên trạm — trùng
    nghĩa thì phải gọi `STEP_NAMES`, đừng gõ lại một bản na ná.
    """
    dam = {m.value for m in State} & set(STEP_NAMES.values())
    assert not dam, "Nhãn đè lên tên trạm: " + ", ".join(sorted(dam))


def test_nhan_vong_chay():
    assert round_label(1) == "Vòng 1"
    assert round_label(12) == "Vòng 12"


def test_hai_von_tu_trong_CUNG_hai_cot(db, make_mo, flow):
    """Cặp cột này cố ý chở hai loại chữ — kiểm cho thấy rõ, đừng vô tình gộp.

    Dòng vòng đời LỆNH ghi mã trạng thái (tra ngược được xuống ENUM của CSDL);
    dòng dưới XƯỞNG ghi tiếng Việt (thợ đọc, chẳng ai tra "PROCESSING").
    """
    code = make_mo()
    flow.accept(code, 0)
    flow.handover(code)
    flow.accept(code, 1)
    flow.accept(code, 2)
    flow.qc(code, "PASS")
    flow.accept(code, 3)
    flow.accept(code, 4)
    flow.run_line(code, "L01")

    from app.common.event_log import repository as event_repo
    from app.modules.mo import repository as mo_repo

    nhat_ky = {e.action: (e.from_state, e.to_state)
               for e in event_repo.events_of(db, mo_repo.get_mo(db, code).id, limit=500)}

    assert nhat_ky["MO_SUBMIT"] == (MoStatus.DRAFT, MoStatus.PROCESSING)
    assert nhat_ky["RUN_START"] == (State.WAITING, State.ASSEMBLING)
    assert nhat_ky["KHO_HANDOVER"] == (STEP_NAMES[0], STEP_NAMES[1])
    assert nhat_ky["ROUND_OPEN"][1] == "Vòng 1"
