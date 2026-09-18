"""Bỏ số mục tài liệu khỏi câu báo lỗi của trigger.

Câu `MO % đã Submit — không sửa được. Huỷ rồi tạo lệnh mới (§4A)` đi THẲNG ra màn
hình người vận hành: `TRIGGER_PREFIXES` trong `app/common/errors.py` bắt tiền tố
`"MO "` rồi giữ nguyên nội dung, vì câu trigger đã kèm sẵn mã lệnh.

`(§4A)` là số mục trong BRD. Người đứng máy không có BRD, không tra được, và nhìn
nó chỉ thấy một mẩu ký hiệu lạ giữa câu tiếng Việt — đúng loại chi tiết làm người
ta bớt tin cái màn hình. Lý do nghiệp vụ vẫn ở nguyên trong mã nguồn và tài liệu,
chỉ không hiện ra cho người dùng nữa.

Sửa bằng migration chứ không sửa file 0006: migration đã chạy thì không chạy lại,
nên hàm trong CSDL vẫn giữ câu cũ. Chỉ `CREATE OR REPLACE` phần thân hàm — không
đụng bảng, không đụng dữ liệu, không khoá gì lâu.

DANH SÁCH CỘT PHẢI CHÉP TỪ KHỐI `upgrade` CỦA 0006, KHÔNG PHẢI `downgrade`. Hai
khối đó gần giống nhau, chỉ khác đúng `pcs_per_box` — chép nhầm thì quy cách hết
bị khoá sau Submit mà không có gì báo, và `CREATE OR REPLACE` ghi đè im lặng.
`tests/test_dong_thung.py::test_quy_cach_luu_va_khoa_cung_sau_submit` canh chỗ này.

Revision ID: 0011
"""

from alembic import op

revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None


def _lock_function_sql(message: str) -> str:
    return f"""
CREATE OR REPLACE FUNCTION mo_lock_after_submit() RETURNS trigger AS $$
BEGIN
  IF OLD.status <> 'DRAFT' AND (
       NEW.code, NEW.product_name, NEW.quantity, NEW.required_production_sec,
       NEW.pcs_per_box)
    IS DISTINCT FROM (
       OLD.code, OLD.product_name, OLD.quantity, OLD.required_production_sec,
       OLD.pcs_per_box) THEN
    RAISE EXCEPTION '{message}', OLD.code;
  END IF;
  RETURN NEW;
END $$ LANGUAGE plpgsql;
"""


NEW_MESSAGE = "MO % đã Submit — không sửa được. Huỷ rồi tạo lệnh mới"
OLD_MESSAGE = "MO % đã Submit — không sửa được. Huỷ rồi tạo lệnh mới (§4A)"


def upgrade() -> None:
    op.execute(_lock_function_sql(NEW_MESSAGE))


def downgrade() -> None:
    op.execute(_lock_function_sql(OLD_MESSAGE))
