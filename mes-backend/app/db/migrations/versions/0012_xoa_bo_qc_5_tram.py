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
    -- 1. Xoá bảng qc_result và kiểu qc_verdict trước
    DROP TABLE IF EXISTS qc_result CASCADE;
    DROP TYPE IF EXISTS qc_verdict CASCADE;

    -- 2. Dọn dẹp ràng buộc khoá ngoại trước khi xoá lý do QC
    UPDATE production SET ng_reason_code_id = NULL 
    WHERE ng_reason_code_id IN (SELECT id FROM reason_code WHERE group_code = 'QC');
    
    UPDATE production SET short_reason_code_id = NULL 
    WHERE short_reason_code_id IN (SELECT id FROM reason_code WHERE group_code = 'QC');
    
    UPDATE line_segment SET hold_reason_code_id = NULL 
    WHERE hold_reason_code_id IN (SELECT id FROM reason_code WHERE group_code = 'QC');

    DELETE FROM reason_code WHERE group_code = 'QC';

    -- 3. Xoá CHECK constraint cũ TRƯỚC KHI cập nhật số liệu
    DO $$
    DECLARE
        r RECORD;
    BEGIN
        FOR r IN (
            SELECT conname
            FROM pg_constraint
            WHERE conrelid = 'mo_round'::regclass AND contype = 'c' AND pg_get_constraintdef(oid) LIKE '%returned_to_step%'
        ) LOOP
            EXECUTE 'ALTER TABLE mo_round DROP CONSTRAINT IF EXISTS ' || quote_ident(r.conname);
        END LOOP;

        FOR r IN (
            SELECT conname
            FROM pg_constraint
            WHERE conrelid = 'mo_step'::regclass AND contype = 'c' AND pg_get_constraintdef(oid) LIKE '%step_no%'
        ) LOOP
            EXECUTE 'ALTER TABLE mo_step DROP CONSTRAINT IF EXISTS ' || quote_ident(r.conname);
        END LOOP;
    END $$;

    -- 4. Xoá bước QC cũ trong mo_step
    DELETE FROM mo_step WHERE step_no = 2;

    -- 5. Đánh số lại các bước cũ trong mo_step theo thứ tự 3->2, 4->3, 5->4
    UPDATE mo_step SET step_no = 2 WHERE step_no = 3;
    UPDATE mo_step SET step_no = 3 WHERE step_no = 4;
    UPDATE mo_step SET step_no = 4 WHERE step_no = 5;

    -- 6. Tạm mở RULE của mo_event để xoá/cập nhật log
    DROP RULE IF EXISTS mo_event_no_delete ON mo_event;
    DROP RULE IF EXISTS mo_event_no_update ON mo_event;

    DELETE FROM mo_event WHERE action IN ('QC_PASS', 'QC_FAIL');
    UPDATE mo_event SET step_no = 2 WHERE step_no = 3;
    UPDATE mo_event SET step_no = 3 WHERE step_no = 4;
    UPDATE mo_event SET step_no = 4 WHERE step_no = 5;

    CREATE RULE mo_event_no_update AS ON UPDATE TO mo_event DO INSTEAD NOTHING;
    CREATE RULE mo_event_no_delete AS ON DELETE TO mo_event DO INSTEAD NOTHING;

    -- 7. Cập nhật returned_to_step trong mo_round (3->2)
    UPDATE mo_round SET returned_to_step = 2 WHERE returned_to_step = 3;

    -- 8. Thêm lại CHECK constraint mới (0..4 cho step_no, 0 hoặc 2 cho returned_to_step)
    ALTER TABLE mo_step ADD CONSTRAINT mo_step_step_no_check CHECK (step_no BETWEEN 0 AND 4);
    ALTER TABLE mo_round ADD CONSTRAINT mo_round_returned_to_step_check CHECK (returned_to_step IN (0, 2));
    """)


def downgrade() -> None:
    pass
