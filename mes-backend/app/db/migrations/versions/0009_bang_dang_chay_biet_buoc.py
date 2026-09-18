"""Bảng đang chạy phải nói được lệnh ĐANG Ở BƯỚC NÀO — BRD §9b.5.

§9b.5 định nghĩa bảng này là "bảng tổng quan để cả xưởng biết đơn hàng đang tới
đâu", và cố ý hiện MO ở **mọi step**. Nhưng `v_round_board` không trả về bước nào
cả — nên bảng hiện đúng mọi lệnh mà không trả lời được chính câu hỏi nó sinh ra để
trả lời.

Hậu quả không chỉ là thiếu một cột. Lệnh vừa tạo còn nằm ở hàng chờ Kho xuất trông
giống hệt lệnh đang lắp ráp dở: cùng `chưa chia` chuyền, cùng `0 phút`, cùng một
dãy gạch ngang. Màn hình thao tác đọc `lines` rỗng rồi suy ra "chưa chia chuyền
thì mời chia" — và mời một lệnh còn chưa ra khỏi kho đi chia chuyền.

`current_step` = bước cao nhất đã quét nhận trong vòng. NULL nghĩa là chưa bước nào
nhận — lệnh vừa chốt, đang nằm ở hàng chờ Kho xuất.

Dùng max() chứ không phải bước chưa đóng: §7b cho Đóng thùng chạy song song với
Sản xuất, nên có lúc hai bước cùng mở. Bước cao nhất là nơi hàng đã tới.

Chỉ dựng lại MỘT view. Không đụng dữ liệu, không khoá bảng.

Revision ID: 0009
"""

from alembic import op

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


_CHUNG = """
DROP VIEW IF EXISTS v_round_board;

CREATE VIEW v_round_board AS
SELECT r.id AS round_id, m.id AS mo_id, m.code, m.product_name, m.quantity,
       r.round_no, r.target_qty, r.required_sec,
       k.actual_sec, k.on_time, k.late_sec,
       p.qty_ok, p.qty_ng, p.qty_short, p.closed_at AS production_closed_at,
       pk.qty_packed, pk.completed_at AS packing_done_at,
       w.handed_over_at,
       {step}
       COALESCE(ln.lines, '[]'::jsonb) AS lines
FROM mo_round r
JOIN manufacturing_order m ON m.id = r.mo_id
LEFT JOIN v_round_kpi k  ON k.round_id  = r.id
LEFT JOIN production  p  ON p.round_id  = r.id
LEFT JOIN packing     pk ON pk.round_id = r.id
LEFT JOIN warehouse_out   w  ON w.round_id  = r.id
LEFT JOIN LATERAL (
  SELECT jsonb_agg(
           jsonb_build_object(
             'line_code',   l.code,
             'current_kind', t.current_kind,
             'hold_reason',  t.hold_reason_text,
             'wait_sec',     t.wait_sec,
             'run_sec',      t.run_sec
           ) ORDER BY l.code
         ) AS lines
  FROM v_line_time t JOIN line l ON l.id = t.line_id
  WHERE t.round_id = r.id
) ln ON TRUE
WHERE r.closed_at IS NULL;
"""

STEP_COL = """(SELECT max(s.step_no) FROM mo_step s WHERE s.round_id = r.id)
         AS current_step,
       """


def upgrade() -> None:
    op.execute(_CHUNG.format(step=STEP_COL))


def downgrade() -> None:
    op.execute(_CHUNG.format(step=""))
