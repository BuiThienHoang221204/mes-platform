"""Khởi tạo lược đồ — chép từ DB-GON.md v2.2 (14 bảng).

Phần CHECK / EXCLUDE / RULE / VIEW viết bằng SQL nguyên văn, KHÔNG diễn đạt qua
API của Alembic — để đối chiếu thẳng với tài liệu (BE-PLAN §9).

Revision ID: 0001
"""

from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


SCHEMA = r"""
-- ══ 1. Kiểu liệt kê ════════════════════════════════════════════════════════
CREATE TYPE mo_status    AS ENUM ('DRAFT','SUBMITTED','PROCESSING','COMPLETED','CANCELLED');
CREATE TYPE qc_verdict   AS ENUM ('PASS','FAIL');
CREATE TYPE segment_kind AS ENUM ('WAIT','RUN');
CREATE TYPE reason_group AS ENUM ('HOLD','NG','SHORT','QC','PACKING');

CREATE EXTENSION IF NOT EXISTS btree_gist;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ══ 2. Danh mục ════════════════════════════════════════════════════════════
CREATE TABLE app_user (
  id        uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  full_name text NOT NULL,
  emp_code  text UNIQUE,
  pin_hash  text,
  roles     text[] NOT NULL DEFAULT '{}',
  is_active boolean NOT NULL DEFAULT true
);

CREATE TABLE line (
  id        smallint PRIMARY KEY,
  code      text NOT NULL UNIQUE,
  name      text,
  is_active boolean NOT NULL DEFAULT true
);

CREATE TABLE reason_code (
  id         smallint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  group_code reason_group NOT NULL,
  name       text NOT NULL,
  is_active  boolean NOT NULL DEFAULT true,
  UNIQUE (group_code, name)
);

-- ══ 3. Lệnh sản xuất ═══════════════════════════════════════════════════════
CREATE TABLE manufacturing_order (
  id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  code         varchar(16) NOT NULL UNIQUE
               CONSTRAINT mo_code_format CHECK (code ~ '^M[0-9]{6}$'),
  product_name text NOT NULL,
  quantity     int  NOT NULL CHECK (quantity > 0),
  unit         text NOT NULL DEFAULT 'PCS',
  required_production_sec int NOT NULL CHECK (required_production_sec > 0),

  status       mo_status NOT NULL DEFAULT 'DRAFT',
  created_by   uuid NOT NULL REFERENCES app_user(id),
  created_at   timestamptz NOT NULL DEFAULT now(),
  submitted_at timestamptz,

  cancelled_at timestamptz,
  cancelled_by uuid REFERENCES app_user(id),
  cancel_reason_text text,

  CONSTRAINT mo_cancel_needs_reason
    CHECK (status <> 'CANCELLED' OR cancel_reason_text IS NOT NULL)
);

-- ══ 4. Trục — lượt chạy ════════════════════════════════════════════════════
CREATE TABLE mo_round (
  id       uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  mo_id    uuid NOT NULL REFERENCES manufacturing_order(id) ON DELETE RESTRICT,
  round_no int  NOT NULL CHECK (round_no >= 1),

  -- Đóng dấu lúc mở vòng, không tính lại về sau
  target_qty   int NOT NULL CHECK (target_qty > 0),
  required_sec int NOT NULL CHECK (required_sec > 0),

  opened_at timestamptz NOT NULL DEFAULT now(),
  closed_at timestamptz,
  returned_to_step   smallint CHECK (returned_to_step IN (0, 3)),
  return_reason_text text,

  UNIQUE (mo_id, round_no),
  CONSTRAINT round_closed_after_open
    CHECK (closed_at IS NULL OR closed_at >= opened_at)
);

-- Mỗi đơn chỉ MỘT lượt đang mở
CREATE UNIQUE INDEX mo_round_one_open ON mo_round (mo_id) WHERE closed_at IS NULL;
CREATE INDEX ON mo_round (mo_id, round_no);

-- ══ 5. Năm trạm — năm sổ, đều 1-1 với vòng ═════════════════════════════════
CREATE TABLE warehouse_out (
  round_id       uuid PRIMARY KEY REFERENCES mo_round(id) ON DELETE CASCADE,
  handed_over_at timestamptz NOT NULL DEFAULT now(),
  handed_over_by uuid NOT NULL REFERENCES app_user(id)
);

CREATE TABLE qc_result (
  round_id   uuid PRIMARY KEY REFERENCES mo_round(id) ON DELETE CASCADE,
  result     qc_verdict NOT NULL,
  checked_at timestamptz NOT NULL DEFAULT now(),
  checked_by uuid NOT NULL REFERENCES app_user(id),
  reason_code_id smallint REFERENCES reason_code(id),
  reason_text    text,

  CONSTRAINT qc_fail_needs_reason
    CHECK (result <> 'FAIL' OR reason_code_id IS NOT NULL OR reason_text IS NOT NULL)
);

CREATE TABLE production (
  round_id  uuid PRIMARY KEY REFERENCES mo_round(id) ON DELETE CASCADE,
  qty_ok    int NOT NULL CHECK (qty_ok    >= 0),
  qty_ng    int NOT NULL CHECK (qty_ng    >= 0),
  qty_short int NOT NULL CHECK (qty_short >= 0),

  ng_reason_code_id    smallint REFERENCES reason_code(id),
  ng_reason_text       text,
  short_reason_code_id smallint REFERENCES reason_code(id),
  short_reason_text    text,

  closed_at timestamptz NOT NULL DEFAULT now(),
  closed_by uuid NOT NULL REFERENCES app_user(id),

  CONSTRAINT prod_has_output CHECK (qty_ok + qty_ng > 0),
  CONSTRAINT ng_needs_reason
    CHECK (qty_ng = 0 OR ng_reason_code_id IS NOT NULL OR ng_reason_text IS NOT NULL),
  CONSTRAINT short_needs_reason
    CHECK (qty_short = 0 OR short_reason_code_id IS NOT NULL OR short_reason_text IS NOT NULL)
);

-- Chốt sổ MỘT LẦN: có dòng rồi thì không sửa được nữa
CREATE RULE production_no_update AS ON UPDATE TO production DO INSTEAD NOTHING;

CREATE TABLE packing (
  round_id     uuid PRIMARY KEY REFERENCES mo_round(id) ON DELETE CASCADE,
  started_at   timestamptz NOT NULL DEFAULT now(),
  started_by   uuid NOT NULL REFERENCES app_user(id),
  qty_packed   int CHECK (qty_packed >= 0),
  note_text    text,
  completed_at timestamptz,
  completed_by uuid REFERENCES app_user(id),

  CONSTRAINT pack_done_consistent
    CHECK ((completed_at IS NULL) = (qty_packed IS NULL))
);

CREATE TABLE warehouse_in (
  round_id     uuid PRIMARY KEY REFERENCES mo_round(id) ON DELETE CASCADE,
  qty_received int CHECK (qty_received >= 0),
  counted_at   timestamptz,
  counted_by   uuid REFERENCES app_user(id)
);

-- ══ 6. Sáu bước của một lượt ═══════════════════════════════════════════════
CREATE TABLE mo_step (
  id       uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  round_id uuid NOT NULL REFERENCES mo_round(id) ON DELETE CASCADE,
  step_no  smallint NOT NULL CHECK (step_no BETWEEN 0 AND 5),

  accepted_at timestamptz NOT NULL DEFAULT now(),
  accepted_by uuid NOT NULL REFERENCES app_user(id),
  closed_at   timestamptz,
  closed_by   uuid REFERENCES app_user(id),

  UNIQUE (round_id, step_no),
  CONSTRAINT step_closed_after_accept CHECK (closed_at IS NULL OR closed_at >= accepted_at),
  CONSTRAINT step_closed_needs_user   CHECK ((closed_at IS NULL) = (closed_by IS NULL))
);
CREATE INDEX ON mo_step (round_id, step_no);

-- ══ 7. Đoạn chuyền — chờ và chạy ═══════════════════════════════════════════
CREATE TABLE line_segment (
  id       uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  round_id uuid NOT NULL REFERENCES mo_round(id) ON DELETE CASCADE,
  line_id  smallint NOT NULL REFERENCES line(id),
  kind     segment_kind NOT NULL,

  started_at timestamptz NOT NULL DEFAULT now(),
  ended_at   timestamptz,
  started_by uuid NOT NULL REFERENCES app_user(id),
  ended_by   uuid REFERENCES app_user(id),

  hold_reason_code_id smallint REFERENCES reason_code(id),
  hold_reason_text    text,

  CONSTRAINT seg_ends_after_start CHECK (ended_at IS NULL OR ended_at > started_at),
  CONSTRAINT seg_reason_only_on_wait
    CHECK (kind = 'WAIT' OR (hold_reason_code_id IS NULL AND hold_reason_text IS NULL))
);

CREATE UNIQUE INDEX seg_one_open
  ON line_segment (round_id, line_id) WHERE ended_at IS NULL;

-- Một chuyền không thể vừa chạy MO này vừa chạy MO kia trong cùng một phút
ALTER TABLE line_segment ADD CONSTRAINT line_run_no_overlap
  EXCLUDE USING gist (
    line_id WITH =,
    tstzrange(started_at, COALESCE(ended_at, 'infinity')) WITH &&
  ) WHERE (kind = 'RUN');

CREATE INDEX ON line_segment (round_id, kind);
CREATE INDEX ON line_segment (line_id, started_at DESC);

-- ══ 8. Sản lượng theo giờ ══════════════════════════════════════════════════
CREATE TABLE hourly_output (
  id       uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  round_id uuid NOT NULL REFERENCES mo_round(id) ON DELETE CASCADE,
  work_date date NOT NULL,
  slot_hour smallint NOT NULL CHECK (slot_hour BETWEEN 0 AND 23),
  qty      int NOT NULL CHECK (qty > 0),
  note     text,
  recorded_by uuid NOT NULL REFERENCES app_user(id),
  recorded_at timestamptz NOT NULL DEFAULT now(),

  UNIQUE (round_id, work_date, slot_hour)
);
CREATE INDEX ON hourly_output (round_id, work_date, slot_hour);

-- ══ 9. Nhật ký — chỉ ghi thêm ══════════════════════════════════════════════
CREATE TABLE mo_event (
  id       bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  mo_id    uuid NOT NULL REFERENCES manufacturing_order(id),
  round_id uuid REFERENCES mo_round(id),
  step_no  smallint,
  action   text NOT NULL,
  from_state  text,
  to_state    text,
  reason_text text,
  actor_id    uuid REFERENCES app_user(id),
  occurred_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX ON mo_event (mo_id, occurred_at DESC);
CREATE INDEX ON mo_event (round_id);
CREATE INDEX ON mo_event (action, occurred_at DESC);

-- ══ 10. Hạ tầng — chống bắn trùng khi quét (KHÔNG thuộc 14 sổ) ═════════════
CREATE TABLE scan_dedupe (
  mo_id      uuid NOT NULL REFERENCES manufacturing_order(id) ON DELETE CASCADE,
  station_no smallint NOT NULL,
  scanned_at timestamptz NOT NULL DEFAULT now(),
  result_message text NOT NULL DEFAULT '',
  PRIMARY KEY (mo_id, station_no)
);
"""

TRIGGERS = r"""
-- ══ Ba số cộng đúng bằng mục tiêu vòng (BRD §7.5) ══════════════════════════
-- CHECK không với tới vì target_qty nằm ở bảng khác.
CREATE OR REPLACE FUNCTION production_balances() RETURNS trigger AS $$
DECLARE t int;
BEGIN
  SELECT target_qty INTO t FROM mo_round WHERE id = NEW.round_id;
  IF NEW.qty_ok + NEW.qty_ng + NEW.qty_short <> t THEN
    RAISE EXCEPTION
      'Đạt % + hỏng % + thiếu % = %, phải đúng bằng SL cần làm của vòng (%)',
      NEW.qty_ok, NEW.qty_ng, NEW.qty_short,
      NEW.qty_ok + NEW.qty_ng + NEW.qty_short, t;
  END IF;
  RETURN NEW;
END $$ LANGUAGE plpgsql;

CREATE TRIGGER trg_production_balance BEFORE INSERT ON production
  FOR EACH ROW EXECUTE FUNCTION production_balances();

-- ══ Đóng gói không vượt SL đạt (BRD §7b) ═══════════════════════════════════
CREATE OR REPLACE FUNCTION packing_within_ok() RETURNS trigger AS $$
DECLARE ok int;
BEGIN
  IF NEW.completed_at IS NOT NULL THEN
    SELECT qty_ok INTO ok FROM production WHERE round_id = NEW.round_id;
    IF ok IS NULL THEN
      RAISE EXCEPTION 'Vòng chưa chốt sổ SX — chưa biết có bao nhiêu hàng đạt để đóng';
    END IF;
    IF NEW.qty_packed > ok THEN
      RAISE EXCEPTION 'Đóng % vượt SL đạt của SX (%)', NEW.qty_packed, ok;
    END IF;
  END IF;
  RETURN NEW;
END $$ LANGUAGE plpgsql;

CREATE TRIGGER trg_packing_within_ok BEFORE INSERT OR UPDATE ON packing
  FOR EACH ROW EXECUTE FUNCTION packing_within_ok();

-- ══ Khoá cứng MO sau Submit (BRD §4A) ══════════════════════════════════════
CREATE OR REPLACE FUNCTION mo_lock_after_submit() RETURNS trigger AS $$
BEGIN
  IF OLD.status <> 'DRAFT' AND (
       NEW.code, NEW.product_name, NEW.quantity, NEW.required_production_sec)
    IS DISTINCT FROM (
       OLD.code, OLD.product_name, OLD.quantity, OLD.required_production_sec) THEN
    RAISE EXCEPTION 'MO % đã Submit — không sửa được. Huỷ rồi tạo lệnh mới (§4A)', OLD.code;
  END IF;
  RETURN NEW;
END $$ LANGUAGE plpgsql;

CREATE TRIGGER trg_mo_lock BEFORE UPDATE ON manufacturing_order
  FOR EACH ROW EXECUTE FUNCTION mo_lock_after_submit();

-- ══ Tổng sản lượng giờ không vượt mục tiêu vòng (BRD §7.2b) ════════════════
CREATE OR REPLACE FUNCTION hourly_within_target() RETURNS trigger AS $$
DECLARE t int; s int;
BEGIN
  SELECT target_qty INTO t FROM mo_round WHERE id = NEW.round_id;
  SELECT COALESCE(SUM(qty), 0) INTO s FROM hourly_output
   WHERE round_id = NEW.round_id AND id <> NEW.id;
  IF s + NEW.qty > t THEN
    RAISE EXCEPTION 'Σ sản lượng giờ % vượt SL cần làm của vòng (%)', s + NEW.qty, t;
  END IF;
  RETURN NEW;
END $$ LANGUAGE plpgsql;

CREATE TRIGGER trg_hourly_cap BEFORE INSERT OR UPDATE ON hourly_output
  FOR EACH ROW EXECUTE FUNCTION hourly_within_target();

-- ══ Nhật ký chỉ ghi thêm (BRD §25A) ════════════════════════════════════════
CREATE RULE mo_event_no_update AS ON UPDATE TO mo_event DO INSTEAD NOTHING;
CREATE RULE mo_event_no_delete AS ON DELETE TO mo_event DO INSTEAD NOTHING;
"""

VIEWS = r"""
-- Thời gian từng bước của từng lượt
CREATE VIEW v_step_time AS
SELECT s.round_id, r.mo_id, r.round_no, s.step_no,
       EXTRACT(EPOCH FROM (COALESCE(s.closed_at, now()) - s.accepted_at))::int AS sec
FROM mo_step s
JOIN mo_round r ON r.id = s.round_id;

-- Cộng dồn một bước qua MỌI LƯỢT của một đơn — con số ở bảng Timer
CREATE VIEW v_step_total AS
SELECT mo_id, step_no, SUM(sec)::int AS sec, COUNT(*)::int AS rounds
FROM v_step_time
GROUP BY mo_id, step_no;

-- Thời gian chờ / chạy của từng chuyền trong một lượt
CREATE VIEW v_line_time AS
SELECT round_id, line_id,
       COALESCE(SUM(EXTRACT(EPOCH FROM (COALESCE(ended_at, now()) - started_at)))
                FILTER (WHERE kind = 'WAIT'), 0)::int AS wait_sec,
       COALESCE(SUM(EXTRACT(EPOCH FROM (COALESCE(ended_at, now()) - started_at)))
                FILTER (WHERE kind = 'RUN'), 0)::int  AS run_sec
FROM line_segment GROUP BY round_id, line_id;

-- KPI thời gian của vòng: §21A lấy chuyền CHẠY LÂU NHẤT
CREATE VIEW v_round_kpi AS
SELECT r.id AS round_id, r.mo_id, r.round_no, r.required_sec,
       MAX(t.run_sec)                               AS actual_sec,
       MAX(t.run_sec) <= r.required_sec             AS on_time,
       GREATEST(0, MAX(t.run_sec) - r.required_sec) AS late_sec
FROM mo_round r JOIN v_line_time t ON t.round_id = r.id
GROUP BY r.id;

-- Tiến độ MO.
-- qty_done đếm SL ĐÃ ĐÓNG GÓI, không phải qty_ok: BRD §6b.2 chốt
-- "qtyDone += SL ĐÃ ĐÓNG GÓI của vòng vừa xong". Hàng đạt mà chưa đóng gói
-- thì chưa nhập kho được, nên chưa tính là xong.
CREATE VIEW v_mo_progress AS
SELECT m.id AS mo_id, m.code, m.quantity,
       COALESCE(SUM(pk.qty_packed), 0)                           AS qty_done,
       COALESCE(SUM(pr.qty_ok), 0)                               AS qty_ok_total,
       COALESCE(SUM(pr.qty_ng), 0)                               AS qty_ng_total,
       COALESCE(SUM(pr.qty_short), 0)                            AS qty_short_total,
       GREATEST(0, m.quantity - COALESCE(SUM(pk.qty_packed), 0)) AS qty_remain,
       COUNT(r.id) FILTER (WHERE r.closed_at IS NOT NULL)        AS rounds_done
FROM manufacturing_order m
LEFT JOIN mo_round   r  ON r.mo_id = m.id
LEFT JOIN production pr ON pr.round_id = r.id
LEFT JOIN packing    pk ON pk.round_id = r.id AND pk.completed_at IS NOT NULL
GROUP BY m.id;

-- Một dòng cho Bảng đang chạy (BRD §7.2)
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

-- Đối soát sản lượng giờ với SX đạt của CHÍNH VÒNG ĐÓ (BRD §7.2b)
CREATE VIEW v_hourly_reconcile AS
SELECT r.id AS round_id, r.mo_id, r.round_no,
       COALESCE(SUM(h.qty), 0) AS hourly_total, p.qty_ok,
       CASE
         WHEN p.qty_ok IS NULL                     THEN 'CHUA_CHOT_SO_SX'
         WHEN COALESCE(SUM(h.qty), 0) = p.qty_ok   THEN 'KHOP'
         WHEN COALESCE(SUM(h.qty), 0) <  p.qty_ok  THEN 'GHI_SOT'
         ELSE 'GHI_DU'
       END AS trang_thai
FROM mo_round r
LEFT JOIN hourly_output h ON h.round_id = r.id
LEFT JOIN production    p ON p.round_id = r.id
GROUP BY r.id, p.qty_ok;
"""


def upgrade() -> None:
    op.execute(SCHEMA)
    op.execute(TRIGGERS)
    op.execute(VIEWS)


def downgrade() -> None:
    op.execute(
        """
        DROP VIEW IF EXISTS v_hourly_reconcile, v_round_board, v_mo_progress,
                            v_round_kpi, v_line_time, v_step_total, v_step_time;
        DROP TABLE IF EXISTS scan_dedupe, mo_event, hourly_output, line_segment, mo_step,
                             warehouse_in, packing, production, qc_result, warehouse_out,
                             mo_round, manufacturing_order, reason_code, line, app_user CASCADE;
        DROP FUNCTION IF EXISTS production_balances, packing_within_ok,
                                mo_lock_after_submit, hourly_within_target CASCADE;
        DROP TYPE IF EXISTS mo_status, qc_verdict, segment_kind, reason_group;
        """
    )
