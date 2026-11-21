"""Ma trận phân quyền BRD §9b — mỗi ô một ca, cộng vài ca đi qua HTTP thật.

Chia hai tầng đúng như code: `permission_for` là nơi RA QUYẾT ĐỊNH (test bằng
tham số, rẻ và đủ dày), `require_step` ở router là nơi THI HÀNH (test qua HTTP,
ít ca nhưng chứng minh dây đã nối).
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.common.errors import Forbidden
from app.common.security.actor import Actor
from app.common.security.permissions import (
    FULL,
    PLANNER,
    ROLE_PERMISSIONS,
    ROLES,
    VIEW,
    department_of,
    permission_for,
)

# ── Tầng 1: bảng luật ───────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "role,step,mong_doi",
    [
        # Phòng nào cũng FULL trạm của mình
        ("WAREHOUSE_OUT_MEMBER", 0, FULL),
        ("SETUP_MEMBER", 1, FULL),
        ("WAITING_MEMBER", 2, FULL),
        ("PRODUCTION_MEMBER", 3, FULL),
        ("WAREHOUSE_IN_MEMBER", 4, FULL),
        # Ai cũng XEM được trạm 3 (Sản xuất) — gồm cả số đóng thùng, vì đóng thùng nằm trong trạm 3
        ("WAREHOUSE_OUT_MEMBER", 3, VIEW),
        ("SETUP_MEMBER", 3, VIEW),
        ("WAREHOUSE_IN_MEMBER", 3, VIEW),
        # Bàn team leader: ngoại lệ DUY NHẤT — FULL trạm 3
        ("WAITING_MEMBER", 3, FULL),
        # Ngoài trạm của mình và trạm 3 thì không thấy gì
        ("SETUP_MEMBER", 0, None),
        ("SETUP_MEMBER", 2, None),
        ("SETUP_MEMBER", 4, None),
        # Tách trách nhiệm: hai kho không với sang nhau được
        ("WAREHOUSE_OUT_MEMBER", 4, None),
        ("WAREHOUSE_IN_MEMBER", 0, None),
        # PLANNER full mọi trạm
        *[(PLANNER, s, FULL) for s in range(5)],
    ],
)
def test_ma_tran_quyen(role: str, step: int, mong_doi: str | None) -> None:
    assert permission_for([role], step) == mong_doi


def test_leader_va_member_hien_QUYEN_Y_HET():
    """BRD §9b.2. Ngày nào tách thì test này đỏ — đúng lúc cần biết."""
    for dept in ROLE_PERMISSIONS:
        for step in range(5):
            lead = permission_for([f"{dept}_LEADER"], step)
            mem = permission_for([f"{dept}_MEMBER"], step)
            assert lead == mem, f"{dept} ở trạm {step}: leader={lead} != member={mem}"


def test_nguoi_nhieu_vai_thi_lay_quyen_CAO_NHAT():
    """Kiêm Setup (view trạm 3) và Bàn team leader (full trạm 3) → được FULL."""
    assert permission_for(["SETUP_MEMBER", "WAITING_MEMBER"], 3) == FULL
    assert permission_for(["WAITING_MEMBER", "SETUP_MEMBER"], 3) == FULL, "không phụ thuộc thứ tự"


def test_PLANNER_luon_FULL_khong_phu_thuoc_vai_khac():
    for step in range(5):
        assert permission_for([PLANNER], step) == FULL
        assert permission_for([PLANNER, "WAREHOUSE_OUT_MEMBER"], step) == FULL


def test_vai_la_thi_khong_co_quyen():
    for vai_la in ("KHO", "ADMIN", "BOSS", "", "_LEADER"):
        assert all(permission_for([vai_la], s) is None for s in range(5)), vai_la


def test_department_of_tach_dung_phan_dau():
    assert department_of("SETUP_MEMBER") == "SETUP"
    assert department_of("WAREHOUSE_OUT_LEADER") == "WAREHOUSE_OUT"
    assert department_of("WAITING_MEMBER") == "WAITING"
    assert department_of(PLANNER) is None
    assert department_of("KHONG_CO_THAT") is None


def test_ROLES_sinh_du_moi_cap_va_PLANNER():
    assert len(ROLES) == len(ROLE_PERMISSIONS) * 2 + 1
    assert PLANNER in ROLES
    assert "SETUP_LEADER" in ROLES and "SETUP_MEMBER" in ROLES


def test_moi_vai_deu_co_it_nhat_mot_tram_xem_duoc():
    for role in ROLES:
        assert any(permission_for([role], s) for s in range(5)), f"{role} không làm được gì"


# ── Tầng 2: thi hành ở Actor (bọc trong session người dùng) ────────────────


def _actor(*roles: str) -> Actor:
    import uuid
    from app.common.security.actor import Actor
    return Actor(user_id=str(uuid.uuid4()), full_name="Người thử", roles=tuple(roles))


def test_actor_require_step_nem_Forbidden_khi_khong_du_quyen():
    with pytest.raises(Forbidden):
        _actor("SETUP_MEMBER").require_step(0)

    with pytest.raises(Forbidden):
        _actor("SETUP_MEMBER").require_step(3, FULL)

    _actor("SETUP_MEMBER").require_step(3, VIEW)   # không ném


def test_actor_require_station_bat_buoc_FULL():
    """`require_station` là `require_step(..., FULL)` — quét là thao tác."""
    _actor("SETUP_MEMBER").require_station(1)
    _actor("WAITING_MEMBER").require_station(3)   # Bàn team leader full trạm 3
    _actor(PLANNER).require_station(0)

    with pytest.raises(Forbidden):
        _actor("SETUP_MEMBER").require_station(3)    # chỉ xem, không quét nhận được


# ── Tầng 3: thi hành qua HTTP thật (dây đã nối tới endpoint) ───────────────


@pytest.fixture
def client():
    """Client giả lập một người dùng cụ thể bằng cách ghi đè dependency.

    Dùng fixture này thì KHÔNG PHẢI tạo người dùng trong CSDL và KHÔNG PHẢI sinh
    JWT: chỉ đổi một biến là cả app tin ngay người gửi request mang vai đó. Nhanh
    gấp 100 lần và không phụ thuộc bảng `app_user`.
    """
    from app.common import deps
    from app.main import app

    hien_tai = {"actor": _actor(PLANNER)}
    app.dependency_overrides[deps.current_actor] = lambda: hien_tai["actor"]

    with TestClient(app) as c:
        c.vai = lambda *roles: hien_tai.update(actor=_actor(*roles))
        yield c

    app.dependency_overrides.clear()


def test_SETUP_khong_ban_giao_kho_duoc(client, make_mo):
    code = make_mo()
    client.vai("SETUP_MEMBER")
    r = client.post(f"/v1/warehouse-out/{code}/handover")
    assert r.status_code == 403
    assert "không thuộc phòng ban" in r.json()["message"]


def test_KHO_VAT_TU_khong_nhap_kho_thanh_pham_duoc(client, make_mo):
    """Lỗ hổng §9b.1: trước đây cùng một vai KHO nên người giao tự nhận được."""
    code = make_mo()
    client.vai("WAREHOUSE_OUT_MEMBER")
    r = client.post(f"/v1/warehouse-in/{code}/complete")
    assert r.status_code == 403


def test_chi_PLANNER_them_va_xoa_chuyen_duoc(client):
    """Danh mục chuyền là dữ liệu gốc — thợ ở trạm không được sửa."""
    client.vai("PRODUCTION_LEADER")
    assert client.post("/v1/lines", json={"code": "L93"}).status_code == 403
    assert client.delete("/v1/lines/L93").status_code == 403

    client.vai(PLANNER)
    r = client.post("/v1/lines", json={"code": "L93", "name": "Chuyền thử"})
    assert r.status_code == 201, r.text
    assert r.json()["code"] == "L93"
    assert client.delete("/v1/lines/L93").status_code == 200


def test_SETUP_khong_dong_goi_duoc_nhung_BAN_CHO_thi_duoc(client, make_mo):
    """Đóng thùng nằm TRONG trạm 3: view trạm 3 không đủ để ghi, full trạm 3 thì đủ."""
    code = make_mo()
    client.vai("SETUP_MEMBER")
    assert client.post(f"/v1/packing/{code}/start").status_code == 403

    client.vai("WAITING_MEMBER")
    r = client.post(f"/v1/packing/{code}/start")
    assert r.status_code != 403, "Bàn team leader có full trạm 3, phải qua được cửa quyền"


def test_ai_cung_xem_duoc_MO_va_bang_dang_chay(client, make_mo):
    code = make_mo()
    for role in ("SETUP_MEMBER", "WAREHOUSE_IN_MEMBER", "SETUP_LEADER"):
        client.vai(role)
        assert client.get(f"/v1/mos/{code}").status_code == 200, role
        assert client.get("/v1/board/running").status_code == 200, role


def test_truy_vet_khong_con_mo_cho_moi_nguoi(client, make_mo):
    code = make_mo()
    client.vai("SETUP_MEMBER")
    assert client.get(f"/v1/mos/{code}/trace").status_code == 200

    client.vai("KHONG_CO_THAT")
    assert client.get(f"/v1/mos/{code}/trace").status_code == 403


def test_MOI_endpoint_deu_khai_bao_quyen():
    import inspect
    from app.main import app

    CO_Y_MO = {
        "/auth/login": "chưa đăng nhập thì lấy đâu ra vai",
        "/auth/refresh": "nt",
        "/auth/logout": "nt",
        "/lines": "danh mục chỉ đọc",
        "/reasons": "danh mục chỉ đọc",
        "/board/running": "bảng tổng quan — §9b.5 nói rõ mọi phòng ban đều xem",
        "/board/queue/{station}": "nt",
        "/board/at/{station}": "nt — cùng dữ liệu, chỉ khác lát cắt đã nhận hay chưa",
        "/board/counts": "nt",
        "/board/overview": "nt — chỉ là /board/running + /board/counts gộp sẵn",
        "/reports/mo-progress": "báo cáo tổng",
        "/reports/hourly": "nt",
        "/healthz": "thăm dò sống chết",
        "/readyz": "nt",
        "/openapi.json": "trang /docs",
        "/docs": "nt",
        "/docs/oauth2-redirect": "nt",
        "/redoc": "nt",
    }
    GAC = ("require_step(", "require_role(", "require_station(")

    def _phang(routes):
        for r in routes:
            sub = getattr(r, "original_router", None)
            if sub is not None:
                yield from _phang(sub.routes)
            else:
                yield r

    kiem_tra = [r for r in _phang(app.routes) if getattr(r, "endpoint", None)]
    assert len(kiem_tra) >= 28

    thieu = [
        r.path
        for r in kiem_tra
        if r.path not in CO_Y_MO and not any(g in inspect.getsource(r.endpoint) for g in GAC)
    ]
    assert not thieu, f"endpoint không khai báo quyền: {thieu}"


# ══ §12.4 — phạm vi XEM của từng trạm ═══════════════════════════════════════
def test_SETUP_khong_doc_duoc_hang_doi_cua_Kho(client):
    client.vai("SETUP_MEMBER")
    assert client.get("/v1/board/queue/0").status_code == 403
    assert client.get("/v1/board/at/0").status_code == 403
    assert client.get("/v1/board/queue/4").status_code == 403


def test_moi_vai_doc_duoc_tram_CUA_MINH(client):
    client.vai("SETUP_MEMBER")
    assert client.get("/v1/board/queue/1").status_code == 200
    assert client.get("/v1/board/at/1").status_code == 200


def test_moi_vai_doc_duoc_tram_3(client):
    """Mọi phòng ban đều View được Step 3 (Sản xuất)."""
    for role in ("WAREHOUSE_OUT_MEMBER", "SETUP_MEMBER", "WAREHOUSE_IN_MEMBER"):
        client.vai(role)
        assert client.get("/v1/board/queue/3").status_code == 200, role
        assert client.get("/v1/board/at/3").status_code == 200, role


def test_PLANNER_doc_duoc_moi_tram(client):
    client.vai(PLANNER)
    for n in range(5):
        assert client.get(f"/v1/board/queue/{n}").status_code == 200, n
        assert client.get(f"/v1/board/at/{n}").status_code == 200, n


def test_bang_dang_chay_va_badge_thi_ca_xuong_deu_xem_duoc(client):
    for role in ("WAREHOUSE_OUT_MEMBER", "SETUP_LEADER", "WAITING_MEMBER"):
        client.vai(role)
        assert client.get("/v1/board/running").status_code == 200, role
        assert client.get("/v1/board/counts").status_code == 200, role
