"""§7.4 [14B] — một chuyền chạy NHIỀU lệnh cùng lúc.

Chuyền là dây chuyền có N chỗ ngồi, không phải một cái máy. Lệnh ít linh kiện chỉ
dùng 5 trong 10 chỗ; 5 người còn lại ngồi làm lệnh khác ngay trên chuyền đó.

Bản 0001 có ràng buộc `line_run_no_overlap` chặn đúng việc này, migration 0008 gỡ.
"""

from __future__ import annotations

from app.common.vocab.enums import SegmentKind
from app.modules.production import repository as production_repo


def _toi_san_xuat(flow, code: str) -> None:
    flow.accept(code, 0)
    flow.handover(code)
    flow.accept(code, 1)
    flow.accept(code, 2)
    flow.qc(code, "PASS")
    flow.accept(code, 3)
    flow.accept(code, 4)


def test_hai_lenh_chay_cung_mot_chuyen(db, make_mo, flow):
    a = make_mo(qty=500, minutes=60)
    b = make_mo(qty=500, minutes=60)
    _toi_san_xuat(flow, a)
    _toi_san_xuat(flow, b)

    flow.run_line(a, "L01")
    flow.run_line(b, "L01")

    for code in (a, b):
        rnd = flow.round_of(code)
        segs = production_repo.segments_of(db, rnd.id)
        dang_chay = [s for s in segs if s.kind == SegmentKind.RUN and s.ended_at is None]
        assert len(dang_chay) == 1, f"{code} phải có đúng một đoạn chạy trên L01"


def test_dung_mot_lenh_khong_keo_lenh_kia_dung_theo(db, make_mo, flow):
    a = make_mo(qty=500, minutes=60)
    b = make_mo(qty=500, minutes=60)
    _toi_san_xuat(flow, a)
    _toi_san_xuat(flow, b)
    flow.run_line(a, "L01")
    flow.run_line(b, "L01")

    flow.hold_line(a, "L01", reason="Hư máy")

    rnd_a = flow.round_of(a)
    assert production_repo.held_line_codes(db, rnd_a.id) == ["L01"]

    rnd_b = flow.round_of(b)
    assert production_repo.held_line_codes(db, rnd_b.id) == [], (
        "lệnh kia vẫn chạy trên chính chuyền đó — dừng phải theo từng LỆNH, không theo chuyền"
    )


def test_hai_lenh_chot_so_doc_lap(db, make_mo, flow):
    a = make_mo(qty=500, minutes=60)
    b = make_mo(qty=500, minutes=60)
    _toi_san_xuat(flow, a)
    _toi_san_xuat(flow, b)
    flow.run_line(a, "L01")
    flow.run_line(b, "L01")

    flow.close_production(a, ok=500)
    row_b = flow.close_production(b, ok=500)
    assert row_b.qty_ok == 500
