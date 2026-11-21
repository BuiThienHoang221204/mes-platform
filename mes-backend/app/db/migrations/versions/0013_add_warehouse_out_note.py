"""Thêm trường ghi chú note_text vào bảng warehouse_out để truyền dặn dò xuống Setup.

Revision ID: 0013
Revises: 0012
"""

from alembic import op
import sqlalchemy as sa

revision = "0013"
down_revision = "0012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("warehouse_out", sa.Column("note_text", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("warehouse_out", "note_text")
