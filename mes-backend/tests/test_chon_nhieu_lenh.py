"""Chốt / huỷ NHIỀU lệnh được tích chọn trên Sổ lệnh.

Cả lô là MỘT đơn vị công việc: một mã hỏng thì không lệnh nào đổi trạng thái.
Nhập một nửa rồi báo lỗi thì người điều độ phải dò xem lệnh nào đã đi, lệnh nào chưa.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.common.security.actor import Actor
from app.common.security.permissions import PLANNER
from app.common.vocab.enums import MoStatus


@pytest.fixture
def client(db, actor):
    from app.common.deps import current_actor
    from app.db.session import get_db
    from app.main import app

    now = {"actor": Actor(user_id=str(actor), full_name="Kế hoạch", roles=(PLANNER,))}
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[current_actor] = lambda: now["actor"]

    with TestClient(app) as c:
        c.vai = lambda *roles: now.update(
            actor=Actor(user_id=str(actor), full_name="Thợ T", roles=roles)
        )
        yield c

    app.dependency_overrides.clear()


@pytest.fixture
def draft(db, actor):
    from app.modules.mo import service as mo_service

    made = {"n": 0}

    def _make(n: int = 1) -> list[str]:
        codes = []
        for _ in range(n):
            made["n"] += 1
            code = f"M7{made['n']:05d}"
            mo_service.create(db, [mo_service.NewMo(code, "Vỏ nhựa F3", 1000, 3600, 0)], actor)
            codes.append(code)
        return codes

    return _make


def _status(db, code: str) -> str:
    from app.modules.mo import repository as mo_repo

    return mo_repo.get_mo(db, code).status


def test_chot_nhieu_lenh_mot_lan(client, db, draft):
    codes = draft(3)

    res = client.post("/v1/mos/submit-batch", json={"codes": codes})

    assert res.status_code == 200, res.text
    assert "3" in res.json()["message"]
    assert all(_status(db, c) == MoStatus.PROCESSING for c in codes)


def test_huy_nhieu_lenh_cung_mot_ly_do(client, db, draft):
    codes = draft(2)

    res = client.post("/v1/mos/cancel-batch", json={"codes": codes, "reason": "Khách dừng đơn"})

    assert res.status_code == 200, res.text
    from app.modules.mo import repository as mo_repo

    for c in codes:
        mo = mo_repo.get_mo(db, c)
        assert mo.status == MoStatus.CANCELLED
        assert mo.cancel_reason_text == "Khách dừng đơn"


def test_mot_ma_hong_thi_ca_lo_quay_dau(client, db, draft):
    codes = draft(3)
    client.post("/v1/mos/submit-batch", json={"codes": [codes[1]]})

    res = client.post("/v1/mos/submit-batch", json={"codes": codes})

    assert res.status_code == 409, res.text
    assert _status(db, codes[0]) == MoStatus.DRAFT
    assert _status(db, codes[2]) == MoStatus.DRAFT


def test_huy_bat_buoc_ghi_ly_do(client, draft):
    codes = draft(1)

    assert client.post("/v1/mos/cancel-batch", json={"codes": codes}).status_code == 422
    assert client.post(
        "/v1/mos/cancel-batch", json={"codes": codes, "reason": "   "}
    ).status_code == 422


def test_danh_sach_rong_bi_chan(client):
    assert client.post("/v1/mos/submit-batch", json={"codes": []}).status_code == 422
    assert client.post(
        "/v1/mos/cancel-batch", json={"codes": [], "reason": "x"}
    ).status_code == 422


def test_ma_sai_dinh_dang_bi_chan_o_bien(client):
    assert client.post("/v1/mos/submit-batch", json={"codes": ["M12345"]}).status_code == 422


def test_ma_trung_trong_danh_sach_bi_chan(client, draft):
    codes = draft(1)

    res = client.post("/v1/mos/submit-batch", json={"codes": codes * 2})

    assert res.status_code == 422, res.text
    assert "trùng" in res.json()["message"]


def test_chi_ke_hoach_chot_duoc(client, draft):
    codes = draft(1)
    client.vai("QC_MEMBER")

    assert client.post("/v1/mos/submit-batch", json={"codes": codes}).status_code == 403
    assert client.post(
        "/v1/mos/cancel-batch", json={"codes": codes, "reason": "x"}
    ).status_code == 403
