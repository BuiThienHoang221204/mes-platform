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
        ("QC_LEADER", 2, FULL),
        ("WAITING_MEMBER", 3, FULL),
        ("PRODUCTION_MEMBER", 4, FULL),
        ("WAREHOUSE_IN_MEMBER", 5, FULL),
        # Ai cũng XEM được trạm 4 — gồm cả số đóng thùng, vì đóng thùng nằm trong trạm 4
        ("WAREHOUSE_OUT_MEMBER", 4, VIEW),
        ("SETUP_MEMBER", 4, VIEW),
        ("QC_MEMBER", 4, VIEW),
        ("WAREHOUSE_IN_MEMBER", 4, VIEW),
        # Bàn team leader: ngoại lệ DUY NHẤT — FULL trạm 4
        ("WAITING_MEMBER", 4, FULL),
        # Ngoài trạm của mình và trạm 4 thì không thấy gì
        ("QC_MEMBER", 0, None),
        ("QC_MEMBER", 1, None),
        ("QC_MEMBER", 3, None),
        ("QC_MEMBER", 5, None),
        ("SETUP_LEADER", 2, None),
        # Tách trách nhiệm: hai kho không với sang nhau được
        ("WAREHOUSE_OUT_MEMBER", 5, None),
        ("WAREHOUSE_IN_MEMBER", 0, None),
        # PLANNER full mọi trạm
        *[(PLANNER, s, FULL) for s in range(6)],
    ],
)
def test_ma_tran_quyen(role: str, step: int, mong_doi: str | None) -> None:
    assert permission_for([role], step) == mong_doi


def test_leader_va_member_hien_QUYEN_Y_HET():
    """BRD §9b.2. Ngày nào tách thì test này đỏ — đúng lúc cần biết."""
    for dept in ROLE_PERMISSIONS:
        for step in range(6):
            assert permission_for([f"{dept}_LEADER"], step) == permission_for(
                [f"{dept}_MEMBER"], step
            ), f"{dept} trạm {step}"


def test_giu_nhieu_vai_thi_lay_muc_CAO_NHAT():
    """Kiêm QC (view trạm 4) và Bàn team leader (full trạm 4) → được FULL."""
    assert permission_for(["QC_MEMBER", "WAITING_MEMBER"], 4) == FULL
    assert permission_for(["WAITING_MEMBER", "QC_MEMBER"], 4) == FULL, "không phụ thuộc thứ tự"


def test_kiem_hai_kho_thi_duoc_ca_hai_dau():
    """Xưởng nhỏ gán cả hai vai kho — hệ thống không chặn, nhưng phải CÓ CHỦ Ý."""
    ca_hai = ["WAREHOUSE_OUT_MEMBER", "WAREHOUSE_IN_MEMBER"]
    assert permission_for(ca_hai, 0) == FULL
    assert permission_for(ca_hai, 5) == FULL


def test_vai_la_thi_khong_co_quyen_gi():
    """Gõ sai tên vai trong CSDL phải thành KHÔNG có quyền, không phải có hết."""
    for vai_la in ("KHO", "ADMIN", "QC_BOSS", "", "_LEADER"):
        assert all(permission_for([vai_la], s) is None for s in range(6)), vai_la


def test_department_of():
    assert department_of("WAREHOUSE_OUT_LEADER") == "WAREHOUSE_OUT"
    assert department_of("QC_MEMBER") == "QC"
    assert department_of(PLANNER) is None
    assert department_of("KHO") is None


# ── Tầng 1b: bảo vệ chính bảng luật ─────────────────────────────────────────
# Hai ca dưới bắt kiểu lỗi không endpoint nào báo — chỉ lộ khi có người đứng ở
# trạm bấm mãi không được.


def test_moi_tram_deu_co_it_nhat_mot_phong_ban_FULL():
    for step in range(6):
        assert any(p.get(step) == FULL for p in ROLE_PERMISSIONS.values()), (
            f"trạm {step} không phòng ban nào thao tác được"
        )


def test_moi_vai_deu_lam_duoc_it_nhat_mot_viec():
    for role in ROLES:
        assert any(permission_for([role], s) for s in range(6)), f"{role} không làm được gì"


def test_dung_13_vai():
    assert len(ROLES) == 13
    assert len(set(ROLES)) == 13, "có vai trùng tên"


# ── Tầng 2: PEP — require_step ──────────────────────────────────────────────


def _actor(*roles: str) -> Actor:
    return Actor(user_id="00000000-0000-0000-0000-000000000000", full_name="Thợ T", roles=roles)


def test_hai_cau_loi_KHAC_NHAU():
    """"Không thuộc phòng ban" và "chỉ được xem" là hai tình huống khác hẳn —
    gộp một câu thì người ở xưởng không biết đi hỏi ai."""
    with pytest.raises(Forbidden) as ngoai_phong:
        _actor("QC_MEMBER").require_step(0)
    assert "không thuộc phòng ban" in str(ngoai_phong.value)

    with pytest.raises(Forbidden) as chi_xem:
        _actor("QC_MEMBER").require_step(4)
    assert "chỉ được XEM" in str(chi_xem.value)


def test_xem_thi_duoc_thao_tac_thi_khong():
    _actor("QC_MEMBER").require_step(4, VIEW)   # không ném
    with pytest.raises(Forbidden):
        _actor("QC_MEMBER").require_step(4, FULL)


def test_quet_QR_theo_tram_cua_thiet_bi():
    """`require_station` là `require_step(..., FULL)` — quét là thao tác."""
    _actor("QC_MEMBER").require_station(2)
    _actor("WAITING_MEMBER").require_station(4)   # Bàn team leader full trạm 4
    _actor(PLANNER).require_station(0)
    with pytest.raises(Forbidden):
        _actor("QC_MEMBER").require_station(4)    # chỉ xem, không quét nhận được


# ── Tầng 3: đi qua HTTP thật ────────────────────────────────────────────────


@pytest.fixture
def client(db):
    """App thật, nhưng CSDL và người dùng thì tiêm vào.

    `vai(...)` đổi người đang đăng nhập giữa chừng để so cùng một endpoint dưới
    hai vai khác nhau mà không phải đăng nhập lại.
    """
    from app.common.deps import current_actor
    from app.db.session import get_db
    from app.main import app

    hien_tai = {"actor": _actor(PLANNER)}
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[current_actor] = lambda: hien_tai["actor"]

    with TestClient(app) as c:
        c.vai = lambda *roles: hien_tai.update(actor=_actor(*roles))
        yield c

    app.dependency_overrides.clear()


def test_QC_khong_ban_giao_kho_duoc(client, make_mo):
    code = make_mo()
    client.vai("QC_MEMBER")
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
    """Danh mục chuyền là dữ liệu gốc — thợ ở trạm không được sửa.

    Kiểm theo VAI chứ không theo trạm: chuyền không thuộc trạm nào cả.
    """
    client.vai("PRODUCTION_LEADER")
    assert client.post("/v1/lines", json={"code": "L93"}).status_code == 403
    assert client.delete("/v1/lines/L93").status_code == 403

    client.vai(PLANNER)
    r = client.post("/v1/lines", json={"code": "L93", "name": "Chuyền thử"})
    assert r.status_code == 201, r.text
    assert r.json()["code"] == "L93"
    assert client.delete("/v1/lines/L93").status_code == 200


def test_QC_khong_dong_goi_duoc_nhung_BAN_CHO_thi_duoc(client, make_mo):
    """Đóng thùng nằm TRONG trạm 4: view trạm 4 không đủ để ghi, full trạm 4 thì đủ."""
    code = make_mo()
    client.vai("QC_MEMBER")
    assert client.post(f"/v1/packing/{code}/start").status_code == 403

    client.vai("WAITING_MEMBER")
    r = client.post(f"/v1/packing/{code}/start")
    assert r.status_code != 403, "Bàn team leader có full trạm 4, phải qua được cửa quyền"


def test_ai_cung_xem_duoc_MO_va_bang_dang_chay(client, make_mo):
    code = make_mo()
    for role in ("QC_MEMBER", "WAREHOUSE_IN_MEMBER", "SETUP_LEADER"):
        client.vai(role)
        assert client.get(f"/v1/mos/{code}").status_code == 200, role
        assert client.get("/v1/board/running").status_code == 200, role


def test_truy_vet_khong_con_mo_cho_moi_nguoi(client, make_mo):
    """Trước đây bất kỳ ai đăng nhập cũng đọc được toàn bộ lịch sử một MO."""
    code = make_mo()
    client.vai("QC_MEMBER")
    assert client.get(f"/v1/mos/{code}/trace").status_code == 200

    # Vai không có quyền nào trên trạm 4 thì bị chặn — hiện chưa có vai nào như
    # vậy, nên dựng một vai giả để chứng minh câu kiểm có tác dụng thật.
    client.vai("KHONG_CO_THAT")
    assert client.get(f"/v1/mos/{code}/trace").status_code == 403


def test_MOI_endpoint_deu_khai_bao_quyen():
    """Sót một endpoint là nó mở toang mà không ai biết.

    Thêm route mới thì test này đỏ cho tới khi khai nó vào một trong hai nhóm —
    ép người thêm phải NÓI RA endpoint đó ai được gọi.
    """
    import inspect

    from app.main import app

    # Cố ý mở cho mọi người đã đăng nhập, kèm lý do.
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
        "/reports/mo-progress": "báo cáo tổng — §9b.5 như /board/*, chỉ có số cộng dồn cả xưởng",
        "/reports/hourly": "nt — không có hàng đợi hay danh sách lệnh của riêng trạm nào",
        "/healthz": "thăm dò sống chết",
        "/readyz": "nt",
        "/openapi.json": "trang /docs",
        "/docs": "nt",
        "/docs/oauth2-redirect": "nt",
        "/redoc": "nt",
    }
    GAC = ("require_step(", "require_role(", "require_station(")

    def _phang(routes):
        """FastAPI 0.141 gộp router LƯỜI — `app.routes` chứa `_IncludedRouter`,
        không phải endpoint. Không mở ra thì test này duyệt đúng 7 route và luôn xanh."""
        for r in routes:
            sub = getattr(r, "original_router", None)
            if sub is not None:
                yield from _phang(sub.routes)
            else:
                yield r

    kiem_tra = [r for r in _phang(app.routes) if getattr(r, "endpoint", None)]
    assert len(kiem_tra) >= 30, f"chỉ thấy {len(kiem_tra)} endpoint — cách duyệt route đã hỏng"

    thieu = [
        r.path
        for r in kiem_tra
        if r.path not in CO_Y_MO and not any(g in inspect.getsource(r.endpoint) for g in GAC)
    ]
    assert not thieu, f"endpoint không khai báo quyền: {thieu}"


# ══ §12.4 — phạm vi XEM của từng trạm ═══════════════════════════════════════
def test_QC_khong_doc_duoc_hang_doi_cua_Kho(client):
    """Giấu nút không phải là phân quyền.

    Sidebar không hiện đường dẫn sang trạm khác, nhưng gõ thẳng URL hay gọi `curl`
    thì trước đây đọc được hàng đợi của mọi phòng ban.
    """
    client.vai("QC_MEMBER")
    assert client.get("/v1/board/queue/0").status_code == 403
    assert client.get("/v1/board/at/0").status_code == 403
    assert client.get("/v1/board/queue/5").status_code == 403


def test_moi_vai_doc_duoc_tram_CUA_MINH(client):
    client.vai("QC_MEMBER")
    assert client.get("/v1/board/queue/2").status_code == 200
    assert client.get("/v1/board/at/2").status_code == 200


def test_moi_vai_doc_duoc_tram_4(client):
    """§9b.4 — mọi phòng ban đều View được Step 4, gồm cả Đóng thùng."""
    for role in ("WAREHOUSE_OUT_MEMBER", "SETUP_MEMBER", "QC_MEMBER", "WAREHOUSE_IN_MEMBER"):
        client.vai(role)
        assert client.get("/v1/board/queue/4").status_code == 200, role
        assert client.get("/v1/board/at/4").status_code == 200, role


def test_PLANNER_doc_duoc_moi_tram(client):
    client.vai(PLANNER)
    for n in range(6):
        assert client.get(f"/v1/board/queue/{n}").status_code == 200, n
        assert client.get(f"/v1/board/at/{n}").status_code == 200, n


def test_bang_dang_chay_va_badge_thi_ca_xuong_deu_xem_duoc(client):
    """§9b.5 — ngoại lệ có chủ đích, không phải sót.

    Giấu bớt thì mỗi tổ mù về công đoạn trước và sau mình, gọi điện hỏi nhau nhiều
    hơn. Cái bị giới hạn là DANH SÁCH lệnh của từng trạm, không phải bức tranh chung.
    """
    for role in ("WAREHOUSE_OUT_MEMBER", "QC_MEMBER", "SETUP_LEADER"):
        client.vai(role)
        assert client.get("/v1/board/running").status_code == 200, role
        assert client.get("/v1/board/counts").status_code == 200, role
