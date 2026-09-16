"""Dữ liệu hệ thống: 14 chuyền + danh mục lý do + tài khoản trạm.

Đây là DỮ LIỆU HỆ THỐNG, thuộc về migration — không phải script chạy tay, vì
thiếu nó thì không trạm nào quét được và không ai ghi được lý do dừng máy.

Revision ID: 0002
"""

import bcrypt
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

# PIN mặc định của mọi tài khoản mẫu là "1234" — ĐỔI TRƯỚC KHI CHẠY THẬT.
# BĂM TẠI CHỖ, không dán chuỗi băm sẵn: chuỗi dán tay không ai kiểm được, và
# bản đầu của file này dán nhầm một chuỗi trông-như-bcrypt nhưng không phải băm
# của "1234" — mọi tài khoản seed không đăng nhập được, mà chỉ lộ ra khi gọi
# thật /auth/login.
PIN_MAC_DINH = "1234"
PIN_1234 = bcrypt.hashpw(PIN_MAC_DINH.encode(), bcrypt.gensalt(rounds=12)).decode()

LINES = "\n".join(
    f"({i}, 'L{i:02d}', 'Chuyền {i:02d}')," for i in range(1, 15)
).rstrip(",")

REASONS = [
    ("HOLD", "Hư máy"),
    ("HOLD", "Kẹt cữ đẩy"),
    ("HOLD", "Hết liệu"),
    ("HOLD", "Đổi ca"),
    ("HOLD", "Mất điện"),
    ("NG", "Lỗi ép nhựa"),
    ("NG", "Lỗi khuôn/gá"),
    ("NG", "Lỗi lắp ráp"),
    ("NG", "Lỗi vật tư đầu vào"),
    ("SHORT", "Chờ bù liệu"),
    ("SHORT", "Hết ca"),
    ("SHORT", "Máy chậm"),
    ("QC", "Sai thông số setup"),
    ("QC", "Lỗi khuôn/gá"),
    ("QC", "Lỗi vật tư đầu vào"),
    ("QC", "Lỗi lắp ráp"),
    ("QC", "Khác"),
    ("PACKING", "Đủ"),
    ("PACKING", "Thiếu thùng"),
    ("PACKING", "Chờ tem"),
]

# Đủ sáu phòng ban + PLANNER, có cả Leader lẫn Member (BRD §9b.7).
# HAI KHO là hai tài khoản khác nhau, hai vai khác nhau — không phải một người
# làm cả hai đầu, đó chính là lớp đối soát §9b.1.
USERS = [
    ("Planner A", "NV001", ["PLANNER"]),
    ("Kho xuất A", "NV010", ["WAREHOUSE_OUT_MEMBER"]),
    ("Setup A", "NV020", ["SETUP_MEMBER"]),
    ("QC1", "NV030", ["QC_MEMBER"]),
    ("Bàn chờ", "NV040", ["WAITING_MEMBER"]),
    ("Leader L1", "NV050", ["PRODUCTION_LEADER"]),
    ("Đóng gói", "NV060", ["PRODUCTION_MEMBER"]),
    ("Kho nhập A", "NV070", ["WAREHOUSE_IN_MEMBER"]),
]


def upgrade() -> None:
    op.execute(f"INSERT INTO line (id, code, name) VALUES\n{LINES};")

    reason_rows = ",\n".join(
        f"('{g}', '{n.replace(chr(39), chr(39) * 2)}')" for g, n in REASONS
    )
    op.execute(f"INSERT INTO reason_code (group_code, name) VALUES\n{reason_rows};")

    def _arr(roles: list[str]) -> str:
        return "ARRAY[" + ", ".join(f"'{r}'" for r in roles) + "]::text[]"

    user_rows = ",\n".join(
        f"('{name}', '{emp}', '{PIN_1234}', {_arr(roles)})" for name, emp, roles in USERS
    )
    op.execute(
        "INSERT INTO app_user (full_name, emp_code, pin_hash, roles) VALUES\n" + user_rows + ";"
    )


def downgrade() -> None:
    op.execute("DELETE FROM app_user WHERE emp_code LIKE 'NV0%';")
    op.execute("DELETE FROM reason_code;")
    op.execute("DELETE FROM line;")
