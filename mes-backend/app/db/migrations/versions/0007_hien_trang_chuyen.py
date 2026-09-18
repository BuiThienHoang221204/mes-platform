"""Hiện trạng chuyền — BRD §7.1 [15A], §7.2, §7.4 [17].

Trước bản này không endpoint nào trả về CHUYỀN NÀO ĐANG CHẠY. `v_line_time` chỉ
cộng dồn `wait_sec` / `run_sec`, còn `v_round_board` không có cột chuyền nào. Nên
Bảng đang chạy thiếu hẳn hai cột mà BRD đòi: `Line` và `Hiện trạng Line`, và người
đứng chuyền không nhìn ra chuyền nào đang chạy — đúng câu hỏi bảng này sinh ra để
trả lời.

Dữ liệu vốn đã đủ: `line_segment.ended_at IS NULL` là đoạn đang mở, `kind` nói đang
chờ hay đang chạy, `hold_reason_text` nói vì sao dừng. Chỉ là chưa ai đọc ra.

Migration này CHỈ dựng lại hai view. Không thêm cột, không sửa dữ liệu, không khoá
bảng — chạy trên CSDL đang có hàng thật cũng an toàn.

Revision ID: 0007
"""

from alembic import op

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


UPGRADE = """
DROP VIEW IF EXISTS v_round_board;
DROP VIEW IF EXISTS v_round_kpi;
DROP VIEW IF EXISTS v_line_time;

-- Thêm trạng thái ĐOẠN ĐANG MỞ vào thời gian cộng dồn của từng chuyền.
-- `seg_one_open` bảo đảm mỗi (vòng, chuyền) chỉ có tối đa một đoạn chưa đóng,
-- nên max() ở đây đọc ra đúng một giá trị chứ không phải gộp nhiều đoạn.
CREATE VIEW v_line_time AS
SELECT round_id, line_id,
       COALESCE(SUM(EXTRACT(EPOCH FROM (COALESCE(ended_at, now()) - started_at)))
                FILTER (WHERE kind = 'WAIT'), 0)::int AS wait_sec,
       COALESCE(SUM(EXTRACT(EPOCH FROM (COALESCE(ended_at, now()) - started_at)))
                FILTER (WHERE kind = 'RUN'), 0)::int  AS run_sec,
       max(kind::text)             FILTER (WHERE ended_at IS NULL) AS current_kind,
       max(hold_reason_text)       FILTER (WHERE ended_at IS NULL) AS hold_reason_text,
       max(started_at)             FILTER (WHERE ended_at IS NULL) AS current_since
FROM line_segment GROUP BY round_id, line_id;

CREATE VIEW v_round_kpi AS
SELECT r.id AS round_id, r.mo_id, r.round_no, r.required_sec,
       MAX(t.run_sec)                               AS actual_sec,
       MAX(t.run_sec) <= r.required_sec             AS on_time,
       GREATEST(0, MAX(t.run_sec) - r.required_sec) AS late_sec
FROM mo_round r LEFT JOIN v_line_time t ON t.round_id = r.id
GROUP BY r.id;

-- Một dòng cho Bảng đang chạy (BRD §7.2), giờ kèm luôn danh sách chuyền.
-- Gộp thành jsonb chứ không nối chuỗi: FE cần vừa mã chuyền vừa trạng thái vừa
-- lý do dừng, nối thành "L01, L02" thì mất hai thứ sau.
CREATE VIEW v_round_board AS
SELECT r.id AS round_id, m.id AS mo_id, m.code, m.product_name, m.quantity,
       r.round_no, r.target_qty, r.required_sec,
       k.actual_sec, k.on_time, k.late_sec,
       p.qty_ok, p.qty_ng, p.qty_short, p.closed_at AS production_closed_at,
       pk.qty_packed, pk.completed_at AS packing_done_at,
       w.handed_over_at,
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

DOWNGRADE = """
DROP VIEW IF EXISTS v_round_board;
DROP VIEW IF EXISTS v_round_kpi;
DROP VIEW IF EXISTS v_line_time;

CREATE VIEW v_line_time AS
SELECT round_id, line_id,
       COALESCE(SUM(EXTRACT(EPOCH FROM (COALESCE(ended_at, now()) - started_at)))
                FILTER (WHERE kind = 'WAIT'), 0)::int AS wait_sec,
       COALESCE(SUM(EXTRACT(EPOCH FROM (COALESCE(ended_at, now()) - started_at)))
                FILTER (WHERE kind = 'RUN'), 0)::int  AS run_sec
FROM line_segment GROUP BY round_id, line_id;

CREATE VIEW v_round_kpi AS
SELECT r.id AS round_id, r.mo_id, r.round_no, r.required_sec,
       MAX(t.run_sec)                               AS actual_sec,
       MAX(t.run_sec) <= r.required_sec             AS on_time,
       GREATEST(0, MAX(t.run_sec) - r.required_sec) AS late_sec
FROM mo_round r LEFT JOIN v_line_time t ON t.round_id = r.id
GROUP BY r.id;

CREATE VIEW v_round_board AS
SELECT r.id AS round_id, m.id AS mo_id, m.code, m.product_name, m.quantity,
       r.round_no, r.target_qty, r.required_sec,
       k.actual_sec, k.on_time, k.late_sec,
       p.qty_ok, p.qty_ng, p.qty_short, p.closed_at AS production_closed_at,
       pk.qty_packed, pk.completed_at AS packing_done_at,
       w.handed_over_at
FROM mo_round r
JOIN manufacturing_order m ON m.id = r.mo_id
LEFT JOIN v_round_kpi k  ON k.round_id  = r.id
LEFT JOIN production  p  ON p.round_id  = r.id
LEFT JOIN packing     pk ON pk.round_id = r.id
LEFT JOIN warehouse_out   w  ON w.round_id  = r.id
WHERE r.closed_at IS NULL;
"""


def upgrade() -> None:
    op.execute(UPGRADE)


def downgrade() -> None:
    op.execute(DOWNGRADE)
