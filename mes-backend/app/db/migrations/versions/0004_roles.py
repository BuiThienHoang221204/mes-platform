"""Bảy vai phẳng → 13 vai theo phòng ban (BRD §9b).

    KHO     → WAREHOUSE_OUT_MEMBER   ← xem cảnh báo bên dưới
    SETUP   → SETUP_MEMBER
    QC      → QC_MEMBER
    BANCHO  → WAITING_MEMBER
    LEADER  → PRODUCTION_MEMBER
    PACKING → PRODUCTION_MEMBER      (đóng gói thuộc phòng Sản xuất, §7b)

Hai chỗ KHÔNG đoán được, phải sửa tay sau khi chạy:

1. `KHO` cũ gộp cả hai kho. Dữ liệu không nói ai thuộc kho nào, nên đổi hết thành
   kho VẬT TƯ. Người của kho THÀNH PHẨM phải gán tay `WAREHOUSE_IN_MEMBER`, không
   thì trạm 5 bấm mãi không được.
2. Ai là Leader. Dữ liệu cũ không có khái niệm đó, nên đổi hết thành MEMBER rồi
   nâng tay vài người. Gán bừa Leader tệ hơn là để tất cả làm Member.

Revision ID: 0004
"""

from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None

# Vai cũ → vai mới. Thứ tự có ý nghĩa: LEADER và PACKING cùng về PRODUCTION.
MAPPING = [
    ("KHO", "WAREHOUSE_OUT_MEMBER"),
    ("SETUP", "SETUP_MEMBER"),
    ("QC", "QC_MEMBER"),
    ("BANCHO", "WAITING_MEMBER"),
    ("LEADER", "PRODUCTION_MEMBER"),
    ("PACKING", "PRODUCTION_MEMBER"),
]


def upgrade() -> None:
    # Thay từng phần tử trong mảng, KHÔNG ghi đè cả mảng: một người có thể giữ
    # nhiều vai cũ (vd Leader kiêm Đóng gói), ghi đè là mất hết trừ vai cuối.
    for old, new in MAPPING:
        op.execute(
            f"UPDATE app_user SET roles = array_replace(roles, '{old}', '{new}') "
            f"WHERE roles @> ARRAY['{old}']::text[];"
        )

    # LEADER + PACKING cùng về PRODUCTION_MEMBER nên mảng có thể trùng lặp — dọn.
    op.execute(
        "UPDATE app_user SET roles = ARRAY("
        "  SELECT DISTINCT unnest(roles) ORDER BY 1"
        ") WHERE array_length(roles, 1) > 1;"
    )

    # PLANNER giữ nguyên tên, không cần đổi.


def downgrade() -> None:
    for old, new in reversed(MAPPING):
        # Không khôi phục được chính xác: PRODUCTION_MEMBER có thể vốn là LEADER
        # hoặc PACKING. Trả về vai cũ ĐẦU TIÊN khớp, chấp nhận mất thông tin.
        op.execute(
            f"UPDATE app_user SET roles = array_replace(roles, '{new}', '{old}') "
            f"WHERE roles @> ARRAY['{new}']::text[];"
        )
    op.execute(
        "UPDATE app_user SET roles = ARRAY("
        "  SELECT DISTINCT unnest(roles) ORDER BY 1"
        ") WHERE array_length(roles, 1) > 1;"
    )
