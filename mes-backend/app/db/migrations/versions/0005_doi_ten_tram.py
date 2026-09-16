"""Đổi tên hai khái niệm theo BRD v2.23.

    Bàn chờ   → Bàn team leader     (trạm 3)
    Đóng gói  → Đóng thùng          (công đoạn song song trong trạm 4)

Chỉ đổi **chữ hiển thị**. Tên kỹ thuật giữ nguyên hết: vai `WAITING_MEMBER`, mã
`RETURN_BANCHO` / `PACK_START` / `PACK_COMPLETE`, bảng `packing`, cột `qty_packed`.
Đổi mã hành động là phá `mo_event` — sổ đó chặn UPDATE/DELETE bằng RULE, nên dòng
cũ và dòng mới sẽ không nối được với nhau nữa.

Việc duy nhất phải làm dưới CSDL là **hai tài khoản mẫu** do `0002` gieo, tên đặt
theo trạm. Không sửa thẳng `0002` vì đó là lịch sử đã chạy — máy nào đã nâng cấp
rồi thì sửa file cũ chẳng có tác dụng gì, mà lại làm hai máy lệch nhau.

Tìm theo `emp_code` chứ không theo `full_name`: mã nhân viên là khoá thật, còn tên
thì có thể đã bị đổi tay từ trước.

Revision ID: 0005
"""

from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None

# emp_code → (tên cũ, tên mới). Tên cũ chỉ để đọc, không dùng trong câu lệnh.
DOI_TEN = [
    ("NV040", "Bàn chờ", "Bàn team leader"),
    ("NV060", "Đóng gói", "Đóng thùng"),
]


def upgrade() -> None:
    for emp_code, _cu, moi in DOI_TEN:
        op.execute(
            f"UPDATE app_user SET full_name = '{moi}' WHERE emp_code = '{emp_code}'"
        )


def downgrade() -> None:
    for emp_code, cu, _moi in DOI_TEN:
        op.execute(
            f"UPDATE app_user SET full_name = '{cu}' WHERE emp_code = '{emp_code}'"
        )
