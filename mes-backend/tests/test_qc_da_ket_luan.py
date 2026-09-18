"""Trạm 2 giữ lệnh cả sau khi ra kết quả — màn hình phải phân biệt được.

Bước chỉ đóng khi trạm SAU quét nhận, nên lệnh đã có kết luận QC vẫn nằm trong
`at_station_rows(2)`. Không có `qc_result` thì màn hình không phân biệt nổi "chưa
kết luận" với "đã kết luận, đang chờ Bàn team leader" — và mời QC kết luận lần hai
cho một vòng đã chốt.
"""

from __future__ import annotations

from app.modules.board import repository as board_repo


def _row(db, code: str) -> dict:
    return next(r for r in board_repo.at_station_rows(db, 2, limit=100) if r["code"] == code)


def _toi_qc(flow, code: str) -> None:
    flow.accept(code, 0)
    flow.handover(code)
    flow.accept(code, 1)
    flow.accept(code, 2)


def test_chua_ket_luan_thi_trong(db, make_mo, flow):
    code = make_mo(qty=1_000, minutes=60)
    _toi_qc(flow, code)
    row = _row(db, code)
    assert row["qc_result"] is None
    assert row["qc_checked_at"] is None


def test_ket_luan_dat_van_con_trong_tay_qc(db, make_mo, flow):
    code = make_mo(qty=1_000, minutes=60)
    _toi_qc(flow, code)
    flow.qc(code, "PASS")

    row = _row(db, code)
    assert row["qc_result"] == "PASS", "đã kết luận nhưng màn hình vẫn thấy trống"
    assert row["qc_checked_at"] is not None


def test_ban_team_leader_nhan_thi_roi_khoi_tram_2(db, make_mo, flow):
    code = make_mo(qty=1_000, minutes=60)
    _toi_qc(flow, code)
    flow.qc(code, "PASS")
    flow.accept(code, 3)

    assert all(r["code"] != code for r in board_repo.at_station_rows(db, 2, limit=100))
