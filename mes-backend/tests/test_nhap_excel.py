"""`POST /mos/import-excel` — nhập nhiều lệnh từ tệp Excel đã tách cột ở trình duyệt.

Nhận danh sách có cấu trúc chứ không nhận văn bản CSV: CSV tách cột bằng dấu phẩy,
mà tên con hàng thật có dấu phẩy. Đường nhập CSV cũ đã gỡ bỏ vì lý do này.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.common.schemas import MAX_IMPORT_ROWS
from app.common.security.actor import Actor
from app.common.security.permissions import PLANNER


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


def _row(n: int, **over):
    body = {
        "code": f"M8{n:05d}",
        "product_name": "Chốt định vị N",
        "quantity": 2000,
        "required_production_sec": 2700,
        "pcs_per_box": 250,
    }
    body.update(over)
    return body


def test_nhap_duoc_nhieu_dong_mot_lan(client):
    res = client.post("/v1/mos/import-excel", json={"items": [_row(1), _row(2), _row(3)]})

    assert res.status_code == 200, res.text
    made = res.json()
    assert [m["code"] for m in made] == ["M800001", "M800002", "M800003"]
    assert made[0]["required_production_sec"] == 2700
    assert made[0]["pcs_per_box"] == 250


def test_ten_co_dau_phay_khong_bi_lech_cot(client):
    """Đúng chỗ CSV hỏng: `split(",")` cắt tên làm đôi rồi đẩy số lượng sang cột sau."""
    ten = "Chốt định vị N, loại 2"
    res = client.post("/v1/mos/import-excel", json={"items": [_row(4, product_name=ten)]})

    assert res.status_code == 200, res.text
    made = res.json()[0]
    assert made["product_name"] == ten
    assert made["quantity"] == 2000


def test_giay_di_thang_khong_lam_tron_qua_phut(client):
    """0,473 giờ = 1702,8 giây. Quy về phút rồi làm tròn là mất 43 giây mỗi lệnh."""
    res = client.post(
        "/v1/mos/import-excel", json={"items": [_row(5, required_production_sec=1703)]}
    )

    assert res.status_code == 200, res.text
    assert res.json()[0]["required_production_sec"] == 1703


def test_thieu_quy_cach_thi_la_khong_dong_thung(client):
    body = _row(6)
    del body["pcs_per_box"]
    res = client.post("/v1/mos/import-excel", json={"items": [body]})

    assert res.status_code == 200, res.text
    assert res.json()[0]["pcs_per_box"] == 0


@pytest.mark.parametrize(
    "over",
    [
        {"code": "M12345"},
        {"code": "XX123456"},
        {"quantity": 0},
        {"quantity": -5},
        {"required_production_sec": 0},
        {"required_production_sec": -60},
        {"pcs_per_box": -1},
        {"product_name": ""},
    ],
)
def test_dong_sai_bi_chan_o_bien(client, over):
    res = client.post("/v1/mos/import-excel", json={"items": [_row(7, **over)]})
    assert res.status_code == 422, f"{over} lọt qua: {res.text}"


def test_danh_sach_rong_bi_chan(client):
    assert client.post("/v1/mos/import-excel", json={"items": []}).status_code == 422


def test_qua_tran_dong_bi_chan(client):
    items = [_row(i) for i in range(MAX_IMPORT_ROWS + 1)]
    assert client.post("/v1/mos/import-excel", json={"items": items}).status_code == 422


def test_ca_lo_hong_thi_khong_ai_duoc_tao(client, db):
    """Một dòng trùng mã là cả lô quay đầu — không nhập một nửa rồi báo lỗi sau."""
    from app.modules.mo import repository as mo_repo

    assert client.post("/v1/mos/import-excel", json={"items": [_row(8)]}).status_code == 200

    res = client.post("/v1/mos/import-excel", json={"items": [_row(9), _row(8), _row(10)]})
    assert res.status_code == 409, res.text

    assert mo_repo.get_mo_or_none(db, "M800008") is not None
    assert mo_repo.get_mo_or_none(db, "M800009") is None
    assert mo_repo.get_mo_or_none(db, "M800010") is None


def test_chi_ke_hoach_nhap_duoc(client):
    client.vai("QC_MEMBER")
    res = client.post("/v1/mos/import-excel", json={"items": [_row(11)]})
    assert res.status_code == 403, res.text
