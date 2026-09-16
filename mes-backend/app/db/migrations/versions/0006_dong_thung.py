"""Đếm THÙNG và ba số mỗi khung giờ — BRD §7.2b + §7b.2, DB-GON §3/§8/§8b.

    manufacturing_order.pcs_per_box   quy cách: bao nhiêu pcs một thùng
    hourly_output.headcount           số người đứng chuyền khung đó
    hourly_output.target_qty          sản lượng YÊU CẦU khung đó
    packing_hourly                    sổ thứ 15 — đếm thùng theo giờ

Ba cột mới đều **NULL được hoặc có DEFAULT**, nên không phải vá dữ liệu cũ. Đó là
điều kiện để migration này chạy trên CSDL đang có hàng thật mà không khoá bảng lâu.

Hai cột giờ để NULL chứ không DEFAULT 0: dòng ghi trước bản này không có hai số đó,
mà điền 0 vào là **bịa ra năng suất chưa ai đo** — báo cáo sẽ đọc thành "giờ đó
không có người nào đứng chuyền".

`pcs_per_box` thì ngược lại, DEFAULT 0 và NOT NULL: 0 có nghĩa thật — *mặt hàng này
không đóng thùng*. Không phải "chưa biết".

Revision ID: 0006
"""

from alembic import op

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


UPGRADE = """
-- ══ 1. Quy cách đóng thùng (BRD §7b.2) ═════════════════════════════════════
ALTER TABLE manufacturing_order
  ADD COLUMN pcs_per_box int NOT NULL DEFAULT 0 CHECK (pcs_per_box >= 0);

-- Quy cách khoá cứng sau Submit y như `quantity`: đổi giữa chừng là mọi dòng
-- thùng đã ghi quy ra một số pcs khác, và sản lượng vòng trước tự đổi theo.
CREATE OR REPLACE FUNCTION mo_lock_after_submit() RETURNS trigger AS $$
BEGIN
  IF OLD.status <> 'DRAFT' AND (
       NEW.code, NEW.product_name, NEW.quantity, NEW.required_production_sec,
       NEW.pcs_per_box)
    IS DISTINCT FROM (
       OLD.code, OLD.product_name, OLD.quantity, OLD.required_production_sec,
       OLD.pcs_per_box) THEN
    RAISE EXCEPTION 'MO % đã Submit — không sửa được. Huỷ rồi tạo lệnh mới (§4A)', OLD.code;
  END IF;
  RETURN NEW;
END $$ LANGUAGE plpgsql;

-- ══ 2. Ba số mỗi khung giờ (BRD §7.2b) ═════════════════════════════════════
ALTER TABLE hourly_output
  ADD COLUMN headcount  int CHECK (headcount  > 0),
  ADD COLUMN target_qty int CHECK (target_qty > 0);

COMMENT ON COLUMN hourly_output.headcount  IS 'Số người đứng chuyền khung giờ đó';
COMMENT ON COLUMN hourly_output.target_qty IS 'Sản lượng YÊU CẦU khung giờ đó';
COMMENT ON COLUMN hourly_output.qty        IS 'Sản lượng THỰC TẾ khung giờ đó';

-- ══ 3. Sổ thứ 15 — đóng thùng theo giờ (BRD §7b.2) ═════════════════════════
CREATE TABLE packing_hourly (
  id       uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  round_id uuid NOT NULL REFERENCES mo_round(id) ON DELETE CASCADE,
  work_date date NOT NULL,
  slot_hour smallint NOT NULL CHECK (slot_hour BETWEEN 0 AND 23),

  -- Chỉ đếm THÙNG ĐẦY. Thùng lẻ chỉ đóng lúc Kết thúc đóng thùng và vào
  -- `packing.qty_packed`, không vào sổ này — nếu không thì phép nhân dưới sai.
  boxes       int NOT NULL CHECK (boxes > 0),

  -- ĐÓNG DẤU quy cách lúc ghi, không đọc sang `manufacturing_order`: quy cách bị
  -- sửa một lần là mọi dòng cũ quy ra số pcs khác. Cùng lý lẽ với `mo_round.target_qty`.
  pcs_per_box int NOT NULL CHECK (pcs_per_box > 0),

  note        text,
  recorded_by uuid NOT NULL REFERENCES app_user(id),
  recorded_at timestamptz NOT NULL DEFAULT now(),

  UNIQUE (round_id, work_date, slot_hour)
);
CREATE INDEX ON packing_hourly (round_id, work_date, slot_hour);

-- ══ 4. Không đóng nhiều hơn số đã LÀM RA (BRD §7b.2) ═══════════════════════
-- Câu lỗi bắt đầu bằng 'Đã đóng ' chứ không 'Đóng ': 'Đóng ' đã là tiền tố của
-- trigger `packing_within_ok`, trùng thì `errors.py` dịch nhầm mã lỗi.
CREATE OR REPLACE FUNCTION packing_hourly_within_made() RETURNS trigger AS $$
DECLARE lam_ra int; da_dong int;
BEGIN
  SELECT qty_ok INTO lam_ra FROM production WHERE round_id = NEW.round_id;
  IF lam_ra IS NULL THEN
    SELECT COALESCE(SUM(qty), 0) INTO lam_ra FROM hourly_output WHERE round_id = NEW.round_id;
  END IF;

  SELECT COALESCE(SUM(boxes * pcs_per_box), 0) INTO da_dong
    FROM packing_hourly WHERE round_id = NEW.round_id AND id <> NEW.id;

  IF da_dong + NEW.boxes * NEW.pcs_per_box > lam_ra THEN
    RAISE EXCEPTION 'Đã đóng % pcs, vượt số đã làm ra của vòng (%)',
      da_dong + NEW.boxes * NEW.pcs_per_box, lam_ra;
  END IF;
  RETURN NEW;
END $$ LANGUAGE plpgsql;

CREATE TRIGGER trg_packing_hourly_cap BEFORE INSERT OR UPDATE ON packing_hourly
  FOR EACH ROW EXECUTE FUNCTION packing_hourly_within_made();

-- ══ 5. Đối soát thùng + HÀNG LẺ đang tồn ═══════════════════════════════════
-- `le_pcs` KHÔNG phải `production.qty_short`: thiếu là chưa làm ra được, phải làm
-- thêm; lẻ là đã làm ra rồi, chỉ chưa gom đủ một thùng.
CREATE VIEW v_packing_reconcile AS
SELECT r.id AS round_id, r.mo_id, r.round_no,
       COALESCE(SUM(ph.boxes), 0)                  AS boxes_total,
       COALESCE(SUM(ph.boxes * ph.pcs_per_box), 0) AS packed_pcs,
       COALESCE(p.qty_ok, h.hourly_total, 0)       AS made_pcs,
       GREATEST(0, COALESCE(p.qty_ok, h.hourly_total, 0)
                   - COALESCE(SUM(ph.boxes * ph.pcs_per_box), 0)) AS le_pcs
FROM mo_round r
LEFT JOIN packing_hourly ph ON ph.round_id = r.id
LEFT JOIN production     p  ON p.round_id  = r.id
LEFT JOIN (SELECT round_id, SUM(qty) AS hourly_total FROM hourly_output GROUP BY round_id) h
       ON h.round_id = r.id
GROUP BY r.id, p.qty_ok, h.hourly_total;
"""

DOWNGRADE = """
DROP VIEW IF EXISTS v_packing_reconcile;
DROP TRIGGER IF EXISTS trg_packing_hourly_cap ON packing_hourly;
DROP FUNCTION IF EXISTS packing_hourly_within_made();
DROP TABLE IF EXISTS packing_hourly;

ALTER TABLE hourly_output DROP COLUMN IF EXISTS target_qty;
ALTER TABLE hourly_output DROP COLUMN IF EXISTS headcount;

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

ALTER TABLE manufacturing_order DROP COLUMN IF EXISTS pcs_per_box;
"""


def upgrade() -> None:
    op.execute(UPGRADE)


def downgrade() -> None:
    op.execute(DOWNGRADE)
