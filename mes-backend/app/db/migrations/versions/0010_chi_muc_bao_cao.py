"""Chỉ mục cho báo cáo sản lượng giờ.

Chỉ mục duy nhất trên `hourly_output` từ `0001_init` là
`(round_id, work_date, slot_hour)` — cột dẫn đầu là `round_id`, hợp với câu hỏi
"vòng này ghi những giờ nào".

Báo cáo hỏi ngược lại: "khoảng ngày này, MỌI vòng, sản lượng ra sao". Vế lọc chỉ
có `work_date`, không có `round_id`, nên chỉ mục cũ vô dụng và Postgres quét toàn
bảng.

Đo trên bảng tạm 500.000 dòng, lọc một tháng:

    chỉ mục cũ   Seq Scan       45,2 ms   ·  7.143 khối đọc
    chỉ mục này  Bitmap Scan    15,3 ms   ·    730 khối đọc

Ước lượng khối lượng thật: 100 lệnh × 16 giờ ≈ 1.600 dòng/ngày, khoảng 500 nghìn
dòng một năm — đúng cỡ vừa đo.

Revision ID: 0010
Revises: 0009
"""

from __future__ import annotations

from alembic import op

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE INDEX ix_hourly_output_work_date ON hourly_output (work_date, slot_hour)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_hourly_output_work_date")
