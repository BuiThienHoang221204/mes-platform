"""Điểm ra quyết định phân quyền (PDP) — MỘT chỗ duy nhất giữ luật RBAC §9b.

Router không tự suy luận, chỉ hỏi `permission_for(...)`. Ngày nào chuyển bảng
quyền xuống CSDL thì sửa ruột hàm này, 30 endpoint không đụng dòng nào.
"""

from __future__ import annotations

# ── Phòng ban = nhóm vai ────────────────────────────────────────────────────
# HAI KHO khác nhau, không phải hai thao tác của một kho (BRD §9b.1):
#   WAREHOUSE_OUT — kho vật tư, giao hàng XUỐNG xưởng      (trạm 0, sổ warehouse_out)
#   WAREHOUSE_IN  — kho thành phẩm, nhận hàng TỪ xưởng lên (trạm 4, sổ warehouse_in)
# Tách rời là cách RBAC hiện thực "tách trách nhiệm": người giao vật tư không
# được tự nhận thành phẩm của chính lô mình giao.
WAREHOUSE_OUT = "WAREHOUSE_OUT"
SETUP = "SETUP"
WAITING = "WAITING"
PRODUCTION = "PRODUCTION"
WAREHOUSE_IN = "WAREHOUSE_IN"

PLANNER = "PLANNER"   # vai điều độ: full mọi trạm, không thuộc phòng ban nào

LEADER, MEMBER = "LEADER", "MEMBER"   # hai cấp, hiện quyền Y HỆT (BRD §9b.2)

# Mức quyền trên một trạm
VIEW = "view"   # chỉ xem
FULL = "full"   # xem + quét nhận + nhập sửa

# Trạm nào thuộc phòng ban nào — dùng khi quét QR, trạm lấy từ token thiết bị.
STATION_DEPARTMENT: dict[int, str] = {
    0: WAREHOUSE_OUT,
    1: SETUP,
    2: WAITING,
    3: PRODUCTION,
    4: WAREHOUSE_IN,
}

# ══ Bảng quyền — TOÀN BỘ luật §9b.4 nằm ở đây, không rải đi đâu khác ════════
ROLE_PERMISSIONS: dict[str, dict[int, str]] = {
    WAREHOUSE_OUT: {0: FULL, 3: VIEW},
    SETUP:         {1: FULL, 3: VIEW},
    WAITING:       {2: FULL, 3: FULL},   # Bàn team leader điều độ và toàn quyền trạm 3
    PRODUCTION:    {3: FULL},
    WAREHOUSE_IN:  {4: FULL, 3: VIEW},
}
# Không có khoá riêng cho Đóng thùng: đóng thùng nằm TRONG trạm 3 (BRD §7b, §9b.4).
# Nên {3: FULL} = ghi được cả `production` lẫn `packing`, {3: VIEW} = xem được cả hai.

# 13 vai, SINH RA từ bảng quyền — thêm phòng ban thì danh sách tự dài ra, không sót.
ROLES: list[str] = [
    f"{dept}_{grade}" for dept in ROLE_PERMISSIONS for grade in (LEADER, MEMBER)
] + [PLANNER]

_SUFFIXES = (f"_{LEADER}", f"_{MEMBER}")


def department_of(role: str) -> str | None:
    """'SETUP_LEADER' → 'SETUP'. Vai lạ hoặc PLANNER → None."""
    return role.rsplit("_", 1)[0] if role.endswith(_SUFFIXES) else None


def full_stations(roles: tuple[str, ...] | list[str]) -> list[int]:
    """Những trạm người này THAO TÁC được, theo thứ tự trạm.

    Người quét cầm điện thoại của mình đi qua nhiều trạm, nên bước không suy được
    từ thiết bị. Suy từ VAI: 8 trong 11 vai chỉ thao tác được đúng một trạm nên
    quét là ra ngay trạm đó. Hai vai đa trạm (Bàn team leader có 2 và 3, PLANNER có
    cả năm) phải tự khai trạm — và `require_station` vẫn kiểm lại.
    """
    return [s for s in STATION_DEPARTMENT if permission_for(roles, s) == FULL]


def permission_for(roles: tuple[str, ...] | list[str], step_no: int) -> str | None:
    """Mức quyền CAO NHẤT người này có trên một trạm. None = không thấy trạm đó.

    Lấy mức cao nhất vì một người giữ được nhiều vai: kiêm Setup và Bàn team leader thì được
    FULL trên trạm 3 nhờ vai Bàn team leader, dù vai Setup chỉ cho VIEW.
    """
    if PLANNER in roles:
        return FULL
    best: str | None = None
    for role in roles:
        dept = department_of(role)
        if dept is None:
            continue   # vai không thuộc phòng ban nào, hoặc tên vai gõ sai
        level = ROLE_PERMISSIONS.get(dept, {}).get(step_no)
        if level == FULL:
            return FULL
        if level == VIEW:
            best = VIEW
    return best
