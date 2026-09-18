"""Một chuyền chạy NHIỀU lệnh cùng lúc — BRD §7.4 [14B].

Bản 0001 đặt `line_run_no_overlap` với lời bình "một chuyền không thể vừa chạy MO
này vừa chạy MO kia trong cùng một phút". Ràng buộc đó hiểu sai chuyền là gì.

**Chuyền không phải một cái máy — nó là dây chuyền có N chỗ ngồi.** Lệnh ít linh
kiện chỉ dùng 5 trong 10 chỗ; 5 chỗ còn lại là 5 người, và họ ngồi làm lệnh khác
ngay trên chuyền đó. Hai lệnh chạy song song trên một chuyền là chuyện bình thường
hằng ngày, không phải xung đột cần chặn.

Ràng buộc cũ khiến thao tác có thật bị từ chối bằng `LINE_BUSY`, và người vận hành
không có cách nào khai đúng việc mình đang làm.

Giữ nguyên `seg_one_open`: mỗi cặp (vòng, chuyền) vẫn chỉ được một đoạn đang mở.
Đó mới là thứ chống ghi trùng — nó khác hẳn việc chặn hai LỆNH khác nhau.

Revision ID: 0008
"""

from alembic import op

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE line_segment DROP CONSTRAINT IF EXISTS line_run_no_overlap;")


def downgrade() -> None:
    op.execute(
        """
        ALTER TABLE line_segment ADD CONSTRAINT line_run_no_overlap
          EXCLUDE USING gist (
            line_id WITH =,
            tstzrange(started_at, COALESCE(ended_at, 'infinity')) WITH &&
          ) WHERE (kind = 'RUN');
        """
    )
