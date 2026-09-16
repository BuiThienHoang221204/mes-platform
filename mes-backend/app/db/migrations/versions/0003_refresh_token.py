"""Bảng `refresh_token` — đăng nhập một lần, đổi access token nhiều lần.

Không thuộc 14 sổ nghiệp vụ. Cùng loại với `scan_dedupe`: hạ tầng, xoá sạch thì
chỉ mất phiên đăng nhập đang mở, không mất dữ liệu sản xuất nào.

Revision ID: 0003
Revises: 0002
"""

from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


SCHEMA = r"""
CREATE TABLE refresh_token (
  id          uuid PRIMARY KEY,
  user_id     uuid NOT NULL REFERENCES app_user(id) ON DELETE CASCADE,

  -- Lưu BĂM, không lưu chuỗi gốc — rò CSDL cũng không dựng lại được token.
  token_hash  text NOT NULL UNIQUE,

  issued_at   timestamptz NOT NULL DEFAULT now(),
  expires_at  timestamptz NOT NULL,

  -- Rỗng = còn dùng được. Có giá trị = đã đổi lấy access mới.
  used_at     timestamptz,
  -- Rỗng = còn hiệu lực. Có giá trị = đăng xuất hoặc bị thu hồi cả chuỗi.
  revoked_at  timestamptz,
  -- Token thay thế nó, để lần ngược cả chuỗi.
  replaced_by uuid REFERENCES refresh_token(id),

  CONSTRAINT refresh_expires_after_issued CHECK (expires_at > issued_at)
);

-- Tra lúc refresh: tìm theo băm.
CREATE INDEX ON refresh_token (user_id);
-- Thu hồi cả chuỗi của một người: quét những token còn sống.
CREATE INDEX refresh_token_con_song
  ON refresh_token (user_id) WHERE revoked_at IS NULL AND used_at IS NULL;
"""


def upgrade() -> None:
    op.execute(SCHEMA)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS refresh_token;")
