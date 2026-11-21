"""Xoá bỏ hoàn toàn QC và đánh số lại 5 trạm liên tục (0..4).

Revision ID: 0012
Revises: 0011
"""

from alembic import op

revision = "0012"
down_revision = "0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
    -- 1. Xoá bản ghi QC cũ trong mo_step và mo_event (nếu có)
    DELETE FROM mo_step WHERE step_no = 2;
    DELETE FROM mo_event WHERE action IN ('QC_PASS', 'QC_FAIL');

    -- 2. Đánh số lại các bước cũ trong mo_step (3->2, 4->3, 5->4)
    UPDATE mo_step SET step_no = 2 WHERE step_no = 3;
    UPDATE mo_step SET step_no = 3 WHERE step_no = 4;
    UPDATE mo_step SET step_no = 4 WHERE step_no = 5;

    -- 3. Đánh số lại trong mo_event
    UPDATE mo_event SET step_no = 2 WHERE step_no = 3;
    UPDATE mo_event SET step_no = 3 WHERE step_no = 4;
    UPDATE mo_event SET step_no = 4 WHERE step_no = 5;

    -- 4. Đánh số lại returned_to_step trong mo_round (3->2)
    UPDATE mo_round SET returned_to_step = 2 WHERE returned_to_step = 3;

    -- 5. Cập nhật CHECK constraint trên mo_step (0..4)
    ALTER TABLE mo_step DROP CONSTRAINT IF EXISTS mo_step_step_no_check;
    ALTER TABLE mo_step ADD CONSTRAINT mo_step_step_no_check CHECK (step_no BETWEEN 0 AND 4);

    -- 6. Cập nhật CHECK constraint trên mo_round (returned_to_step IN (0, 2))
    ALTER TABLE mo_round DROP CONSTRAINT IF EXISTS mo_round_returned_to_step_check;
    ALTER TABLE mo_round ADD CONSTRAINT mo_round_returned_to_step_check CHECK (returned_to_step IN (0, 2));

    -- 7. Xoá bảng qc_result và kiểu qc_verdict
    DROP TABLE IF EXISTS qc_result CASCADE;
    DROP TYPE IF EXISTS qc_verdict;

    -- 8. Xoá các lý do thuộc nhóm QC trong reason_code
    DELETE FROM reason_code WHERE group_code = 'QC';
    """)


def downgrade() -> None:
    pass
