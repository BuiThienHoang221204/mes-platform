# MES Platform — Cơ sở dữ liệu (PostgreSQL) · 15 sổ + 2 bảng hạ tầng

> Bản v2.0 — 2026-09-13
> Căn cứ: `BRD-v2-chot.md` v2.23 + `demo/mes-v2-console.html` v47
> Sơ đồ và giải thích: `demo/db-model-gon.html`
> Đích: PostgreSQL 15+
>
> **v2.9 — 2026-09-15:** migration `0006` đã chạy — ba phần của v2.7/v2.8 giờ **có thật** trong CSDL.
> Backend cũng đã có: model `PackingHourly`, `POST /v1/packing/{code}/hourly`, ba số bắt buộc ở
> `POST /v1/hourly/{code}`, `pcs_per_box` ở `POST /v1/mos` và cột 5 tuỳ chọn của CSV.
>
> **v2.8 — 2026-09-15:** bắt kịp BRD v2.22 — **`manufacturing_order.pcs_per_box`** (quy cách,
> §3) · **sổ thứ 15 `packing_hourly`** đếm thùng theo giờ (§8b) · trigger `packing_hourly_within_made`
> (§10.5) · view `v_packing_reconcile` (§11). Quy cách bị **khoá cứng sau Submit** nên vào luôn trigger
> `mo_lock_after_submit` (§10.3).
>
> **v2.7 — 2026-09-15:** bắt kịp BRD v2.21 — `hourly_output` thêm **`headcount`** và **`target_qty`**
> (§8). Hai cột NULL được: bản ghi có trước v2.21 không có hai số này, và đoán một con số vào đó là
> bịa ra năng suất chưa ai đo.
>
> **v2.6 — 2026-09-14:** đổi tên hai sổ kho cho ĐỐI XỨNG — `warehouse_out` → `warehouse_out`
> (kho vật tư, trạm 0) và `warehouse_in` → `warehouse_in` (kho thành phẩm, trạm 5). Đây là **hai kho
> vật lý khác nhau** (BRD §9b.1); tên cũ không đối xứng nên đọc `warehouse_out` dễ tưởng là "cái kho".
>
> **v2.5 — 2026-09-14:** đối chiếu với migration đang chạy, sửa 6 chỗ tài liệu nói sai:
> `v_mo_progress` tính theo `packing.qty_packed` (§11) · thêm §9c `refresh_token` ·
> `roles` cập nhật theo BRD §9b · đoạn chuyền dùng `clock_timestamp()` (§7) ·
> `app_user` thiếu cột `pin_hash` · ràng buộc mã MO phải đặt tên `mo_code_format`.
>
> **v2.4 — 2026-09-14:** đổi tên bảng `dispatch` → `warehouse_out` cho khớp trạm 0 (Kho)
> và khớp thư mục `app/warehouse_out/` bên BE.
>
> **v2.3 — 2026-09-14:** thêm §9b `scan_dedupe` — bảng hạ tầng đã có trong migration
> nhưng tài liệu chưa nói tới. DB thật có **15** bảng, không phải 14.
>
> **v2.2 — 2026-09-13:** thêm `v_step_time` · `v_step_total` cho Timer cộng dồn qua mọi lượt (§6).
>
> **v2.1 — 2026-09-13:** §3 bỏ thao tác In phiếu, `warehouse_out` (lúc đó tên `dispatch`) từ 6 ô còn **2**.
>
> **Đổi so với v1.0 (9 bảng):** năm nhóm ô của năm trạm tách thành năm bảng riêng —
> `warehouse_out` · `qc_result` · `production` · `packing` · `warehouse_in`. `mo_round` từ 35 ô còn **9**.
> Lý do: thêm trạm về sau là `CREATE TABLE`, không phải `ALTER TABLE` bảng chính.

---

## 0. Bản đồ 15 sổ + 2 bảng hạ tầng

> **Toàn bộ tài liệu này đã khớp với migration đang chạy** (tới `0006`), đối chiếu thẳng với
> `information_schema`. Ba phần mới nhất — `manufacturing_order.pcs_per_box` (§3) ·
> `hourly_output.headcount`/`target_qty` (§8) · sổ `packing_hourly` cùng trigger §10.5 và view
> `v_packing_reconcile` (§8b, §11) — vào CSDL ở migration `0006`, có `downgrade()` đã thử lùi rồi
> tiến lại.

| Nhóm | Bảng | Vai trò |
|---|---|---|
| **Danh mục** | `app_user` · `line` · `reason_code` | Thứ tồn tại sẵn, được tra tới |
| **Lệnh** | `manufacturing_order` | Bất biến sau Submit |
| **Trục** | `mo_round` | Một lần đơn xuống xưởng |
| **Mỗi trạm một sổ** | `warehouse_out` · `qc_result` · `production` · `packing` · `warehouse_in` | Dữ liệu trạm đó sinh ra |
| **Chi tiết trong vòng** | `mo_step` · `line_segment` · `hourly_output` · `packing_hourly` | Nhiều dòng mỗi vòng |
| **Nhật ký** | `mo_event` | Chỉ ghi thêm |
| *(hạ tầng)* | `scan_dedupe` | **Không phải sổ** — chống đầu đọc bắn trùng, §9b |
| *(hạ tầng)* | `refresh_token` | **Không phải sổ** — phiên đăng nhập, §9c |

Hai bảng hạ tầng **không nằm trong sơ đồ ERD** (`demo/db-model-gon.html`) và đó là cố ý: chúng không
mang quan hệ nghiệp vụ nào — một cái là bộ nhớ đệm 2 giây, một cái là phiên đăng nhập. Nhưng cả hai
đều CÓ trong migration, nên `\dt` trên DB thật trả về **17** bảng (18 nếu tính `alembic_version`)
— đã đối chiếu thẳng với `information_schema`.

**Năm bảng trạm đều 1-1 với vòng:** `round_id` vừa là khoá chính vừa là khoá ngoại. Một vòng không thể
có hai lần phát lệnh, hai kết quả QC, hai lần chốt sổ SX. **Có dòng nghĩa là việc đó đã xảy ra** — không
cần cột "đã làm chưa".

---

## 1. Quy ước

| Quy ước | Ví dụ |
|---|---|
| Thời điểm `_at`, người `_by` | `closed_at`, `closed_by` |
| Số lượng `qty_` | `qty_ok`, `qty_packed` |
| Lý do đi thành cặp: mã + chữ | `ng_reason_code_id` + `ng_reason_text` |
| Cờ `is_` | `is_active` |

**Mọi `_at` là `timestamptz`** — xưởng chạy qua đêm, lưu không kèm múi giờ là tự chuốc lỗi.

**Mỗi lý do một cặp ô.** Ô mã để thống kê (*tháng này dừng vì hư máy mấy lần*), ô chữ để giữ nguyên văn.
Danh mục không bao giờ phủ hết mọi tình huống.

```sql
CREATE TYPE mo_status    AS ENUM ('DRAFT','SUBMITTED','PROCESSING','COMPLETED','CANCELLED');
CREATE TYPE qc_verdict   AS ENUM ('PASS','FAIL');
CREATE TYPE segment_kind AS ENUM ('WAIT','RUN');
CREATE TYPE reason_group AS ENUM ('HOLD','NG','SHORT','QC','PACKING');

CREATE EXTENSION IF NOT EXISTS btree_gist;
```

---

## 2. Danh mục — 3 bảng

```sql
CREATE TABLE app_user (
  id        uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  full_name text NOT NULL,
  emp_code  text UNIQUE,
  pin_hash  text,                           -- bcrypt; rỗng = tài khoản chưa đặt PIN
  roles     text[] NOT NULL DEFAULT '{}',   -- 13 vai, xem BRD §9b.7
  is_active boolean NOT NULL DEFAULT true
);

CREATE TABLE line (
  id        smallint PRIMARY KEY,
  code      text NOT NULL UNIQUE,           -- 'L01' … 'L14'
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
```

> `roles` là mảng chứ không phải bảng nối: xưởng nhỏ, một người kiêm hai phòng ban là bình thường.

**13 vai** (BRD §9b, chốt 2026-09-14) — 6 phòng ban × 2 cấp + PLANNER:

```
WAREHOUSE_OUT_LEADER   WAREHOUSE_OUT_MEMBER   ← Kho XUẤT, trạm 0 · kho vật tư
SETUP_LEADER           SETUP_MEMBER           ← trạm 1
QC_LEADER              QC_MEMBER              ← trạm 2
WAITING_LEADER         WAITING_MEMBER         ← Bàn team leader, trạm 3 · có FULL quyền trạm 4
PRODUCTION_LEADER      PRODUCTION_MEMBER      ← trạm 4, gồm cả Đóng thùng
WAREHOUSE_IN_LEADER    WAREHOUSE_IN_MEMBER    ← Kho NHẬP, trạm 5 · kho thành phẩm
PLANNER                                       ← full mọi trạm
```

Kho xuất (0) và Kho nhập (5) là **hai phòng ban riêng** — trước gộp chung một vai `KHO`, nghĩa là
người giao vật tư tự nhận luôn thành phẩm của chính lô mình giao.

Leader và Member **hiện quyền y hệt nhau**; tách sẵn để sau siết không phải sửa dữ liệu tài khoản.

**Đã vào code** (2026-09-14): danh sách vai này *sinh ra* từ bảng quyền trong
`app/common/permissions.py`, không gõ tay ở hai chỗ. Migration `0004_roles` đổi `app_user.roles`
từ 7 vai phẳng sang 13 vai trên.

> Quyền vẫn kiểm ở tầng ứng dụng. Muốn siết thêm ở tầng CSDL thì làm được ngay — mỗi sổ trạm là
> một bảng riêng nên `GRANT SELECT, INSERT ON qc_result TO qc_role` là đủ. Chưa cần, vì backend
> đang là đường vào duy nhất.

---

## 3. Lệnh sản xuất

```sql
CREATE TABLE manufacturing_order (
  id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  code         text NOT NULL UNIQUE,
  product_name text NOT NULL,
  quantity     int  NOT NULL CHECK (quantity > 0),
  unit         text NOT NULL DEFAULT 'PCS',
  -- Quy cách đóng thùng (BRD §7b.2). 0 = mặt hàng không đóng thùng.
  pcs_per_box  int  NOT NULL DEFAULT 0 CHECK (pcs_per_box >= 0),
  required_production_sec int NOT NULL CHECK (required_production_sec > 0),

  status       mo_status NOT NULL DEFAULT 'DRAFT',
  created_by   uuid NOT NULL REFERENCES app_user(id),
  created_at   timestamptz NOT NULL DEFAULT now(),
  submitted_at timestamptz,

  cancelled_at timestamptz,
  cancelled_by uuid REFERENCES app_user(id),
  cancel_reason_text text,

  CONSTRAINT mo_code_format CHECK (code ~ '^M[0-9]{6}$'),
  CONSTRAINT mo_cancel_needs_reason
    CHECK (status <> 'CANCELLED' OR cancel_reason_text IS NOT NULL)
);
```

- **`quantity` bất biến** (§2.1) — kế hoạch và thực tế phải nằm hai chỗ thì mới so được.
- **Mã chặn ngay ở DB** (§2.2). Chặn ở tầng ứng dụng thôi không đủ: import CSV, script vá dữ liệu, nhập
  tay — chỉ DB mới chặn được cả ba đường.
- **Mọi ràng buộc đều ĐẶT TÊN**, kể cả khi viết một dòng được. Backend tra theo tên đó để đổi lỗi của
  Postgres thành câu tiếng Việt (`mo_code_format` → *"Mã MO phải là chữ M kèm đúng 6 chữ số"*). Ràng buộc
  không tên thì Postgres tự đặt kiểu `manufacturing_order_code_check`, đổi lược đồ là tên đổi theo và
  bảng ánh xạ lỗi gãy âm thầm.
- **Không hard delete** (§4A): nhập sai sau Submit → `CANCELLED` kèm lý do rồi tạo lệnh mới.
- **`pcs_per_box` là cầu nối DUY NHẤT giữa hai đơn vị** (§7b.2). Đơn hàng đặt bằng PCS, xưởng đóng gói
  đếm bằng THÙNG. Mọi phép tính tiến độ vẫn chạy bằng pcs — thùng chỉ là cách đếm cho nhanh.
  Nó **khoá cứng sau Submit** y như `quantity`, nên nằm trong trigger `mo_lock_after_submit` (§10.3):
  đổi quy cách giữa chừng là mọi dòng thùng đã ghi quy ra một số pcs khác.

---

## 4. Trục — lượt chạy

```sql
CREATE TABLE mo_round (
  id       uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  mo_id    uuid NOT NULL REFERENCES manufacturing_order(id) ON DELETE RESTRICT,
  round_no int  NOT NULL CHECK (round_no >= 1),

  -- ĐÓNG DẤU lúc mở vòng, không tính lại về sau (§6b.2, §7.3)
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

-- §6b mỗi đơn chỉ một lượt đang mở
CREATE UNIQUE INDEX mo_round_one_open ON mo_round (mo_id) WHERE closed_at IS NULL;
CREATE INDEX ON mo_round (mo_id, round_no);
```

**Chín cột, hết.** Đây là toàn bộ sự thật ở mức vòng: vòng thứ mấy, phải làm bao nhiêu, được bao nhiêu
giây, mở lúc nào, đóng lúc nào, trả về bước nào và vì sao.

> **Vì sao đóng dấu `target_qty` và `required_sec` chứ không tính lại:** tính lại thì mỗi lần mở báo cáo
> ra một số khác — KPI tháng trước sẽ tự đổi khi tháng này chạy thêm. Đóng dấu là chốt luật chơi ngay lúc
> giao việc.

> **`returned_to_step` chỉ nhận 0 hoặc 3.** `3` khi thiếu SL hoặc line dừng quá lâu — máy đã setup đúng,
> hàng đã qua QC. `0` khi QC FAIL — setup sai thì phải in phiếu mới, chỉnh máy, QC kiểm lại từ gốc.

---

## 5. Năm trạm — năm sổ

Cả năm dùng chung một khuôn: `round_id` vừa là khoá chính vừa là khoá ngoại, `ON DELETE CASCADE`.

### 5.1 `warehouse_out` — Kho vật tư bàn giao (§3)

```sql
CREATE TABLE warehouse_out (
  round_id       uuid PRIMARY KEY REFERENCES mo_round(id) ON DELETE CASCADE,
  handed_over_at timestamptz NOT NULL DEFAULT now(),
  handed_over_by uuid NOT NULL REFERENCES app_user(id)
);
```

**Hai ô, hết.** §3 bỏ thao tác In phiếu nên không còn `first_printed_at` · `printed_by` ·
`print_count`, và ràng buộc *"chưa in thì không bàn giao"* cũng không còn gì để chặn.

Mốc *Kho quét nhận lệnh* nằm ở `mo_step` bước 0 — bảng này chỉ giữ đúng cái `mo_step` không biết:
**hàng rời kho lúc nào, ai giao**. Có dòng = đã bàn giao; chưa có dòng = Setup chưa được nhận.

### 5.2 `qc_result` — QC (§5)

```sql
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
```

**Kết quả QC gắn theo vòng.** Sang vòng mới là dòng mới — kết quả cũ vẫn nằm nguyên ở vòng cũ, không bị
xoá, không lẫn sang.

### 5.3 `production` — chốt sổ Sản xuất (§7.5)

```sql
CREATE TABLE production (
  round_id  uuid PRIMARY KEY REFERENCES mo_round(id) ON DELETE CASCADE,
  qty_ok    int NOT NULL CHECK (qty_ok    >= 0),   -- ĐẠT   → cộng vào tiến độ MO
  qty_ng    int NOT NULL CHECK (qty_ng    >= 0),   -- HỎNG  → làm ra rồi nhưng hỏng
  qty_short int NOT NULL CHECK (qty_short >= 0),   -- THIẾU → không làm ra được

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

-- §7.5 chốt sổ MỘT LẦN: có dòng rồi thì không sửa được nữa
CREATE RULE production_no_update AS ON UPDATE TO production DO INSTEAD NOTHING;
```

> **Ràng buộc ba số cộng bằng `target_qty` phải là trigger** (§9.1), vì `target_qty` nằm ở `mo_round`.
> Đây là cái giá của việc tách bảng — đổi lại, "chốt sổ một lần" trở thành **một `RULE` một dòng** thay
> vì trigger so sánh cột.

### 5.4 `packing` — đóng thùng, chạy song song (§7b)

```sql
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
```

**Không có cột SL hỏng** — hàng xuống tới đóng thùng là hàng đã đạt, hỏng khai ở `production` rồi (§7.5).
`note_text` là ghi chú tự do (`Đủ`, `thiếu thùng`, `chờ tem`), **không gọi là "lý do"**: đóng thùng thường
chẳng có sự cố gì, gọi vậy khiến người nhập tưởng phải có vấn đề mới được ghi.

**Đây là bảng được lợi nhiều nhất khi tách ra.** §7b cho đóng thùng chạy **song song** với chuyền — hai
người, hai thời điểm. Để chung một dòng với `production` thì hai bên ghi đè nhau là rủi ro thật.

### 5.5 `warehouse_in` — Kho thành phẩm nhận hàng (§8)

```sql
CREATE TABLE warehouse_in (
  round_id     uuid PRIMARY KEY REFERENCES mo_round(id) ON DELETE CASCADE,
  qty_received int CHECK (qty_received >= 0),
  counted_at   timestamptz,
  counted_by   uuid REFERENCES app_user(id)
);
```

BRD không bắt kho đếm lại, nhưng đây là **chỗ duy nhất phát hiện thất thoát** giữa đóng thùng và kho. Có
dòng = kho đã đếm; không có dòng = kho nhận theo số đóng thùng.

> Mốc *quét nhận* và *đóng bước* của cả sáu bước nằm ở `mo_step`, **không chép lại vào các bảng trạm**.
> Lưu hai nơi thì có ngày hai nơi lệch nhau và không ai biết nơi nào đúng.

---

## 6. Sáu bước của một lượt

```sql
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
```

**`closed_by` là cột đáng giá nhất để truy cứu.** Hệ thống bỏ nút Complete: bước N đóng khi **bước N+1
quét nhận** (§9). Không có cột này thì tranh chấp *"Setup xong lâu rồi mà QC không nhận"* không ai phân
xử được.

**Thêm trạm thứ 7:** nới `CHECK step_no BETWEEN 0 AND 6`, rồi `CREATE TABLE` cho dữ liệu riêng của trạm
đó. Không `ALTER` bảng nào đang chứa dữ liệu sản xuất.

**Một bước có thể có nhiều dòng — mỗi lượt một dòng.** Nên có hai cách đọc, cả hai đều cần:

| Câu hỏi | Lấy ở đâu |
|---|---|
| Lượt 2 nằm ở Setup bao lâu? | một dòng `v_step_time` |
| Cả đơn tốn bao nhiêu thời gian ở Setup? | `v_step_total` — cộng mọi lượt, kèm số lượt |

Thiếu cách thứ hai thì đơn qua Setup ba lần vẫn hiện `—` nếu lượt cuối không qua Setup.

---

## 7. Đoạn chuyền — chờ và chạy

```sql
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
```

**Một bảng trả lời cả ba câu:** TG thực tế là tổng đoạn `RUN`; TG chờ là tổng đoạn `WAIT`; đang dừng hay
không nhìn đoạn mới nhất, và lý do ghi ngay trên chính đoạn đó.

> **Mốc đóng/mở đoạn phải lấy bằng `clock_timestamp()`, KHÔNG phải `now()`.**
> `now()` trả giờ **bắt đầu giao dịch** và không nhúc nhích trong suốt transaction. Gán chuyền rồi cho
> chạy trong cùng một giao dịch sẽ sinh đoạn có `started_at = ended_at`, vi phạm `seg_ends_after_start`.
> Lỗi này chỉ lộ ra khi chạy test — ngoài thực tế mỗi thao tác là một request riêng nên `now()` khác nhau.

**Hai luật BRD tự đúng:** một MO chạy nhiều chuyền (§7.1) là nhiều dòng cùng `round_id` khác `line_id`;
một chuyền ôm nhiều MO (§14B) là nhiều dòng cùng `line_id` khác `round_id` — **không** unique trên
`line_id`.

---

## 8. Sản lượng theo giờ

```sql
CREATE TABLE hourly_output (
  id       uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  round_id uuid NOT NULL REFERENCES mo_round(id) ON DELETE CASCADE,
  work_date date NOT NULL,
  slot_hour smallint NOT NULL CHECK (slot_hour BETWEEN 0 AND 23),

  -- Ba số mỗi khung giờ (BRD §7.2b).
  -- Cả hai NULL được: dòng ghi trước v2.21 không có chúng, mà suy ngược một con số
  -- vào đó là bịa ra năng suất chưa ai đo.
  headcount  int CHECK (headcount  > 0),   -- số người đứng chuyền khung đó
  target_qty int CHECK (target_qty > 0),   -- sản lượng YÊU CẦU của khung đó
  qty        int NOT NULL CHECK (qty > 0), -- sản lượng THỰC TẾ
  note     text,
  recorded_by uuid NOT NULL REFERENCES app_user(id),
  recorded_at timestamptz NOT NULL DEFAULT now(),

  UNIQUE (round_id, work_date, slot_hour)    -- §7.2b mỗi khung mỗi ngày một lần
);
```

Ghi **theo MO** chứ không theo chuyền (§7.2b). Có `work_date` riêng — thiếu nó thì đơn chạy qua đêm
không ghi được khung `08:00-09:00` lần thứ hai. **Không tác động** tới đồng hồ hay KPI; nó tồn tại để
đối soát với `production.qty_ok` — hai nguồn độc lập, lệch nhau là có chuyện (§10 #29).

**Ba số, không phải một** (§7.2b). Riêng `qty` thì 500 cái một giờ là nhanh hay chậm không ai biết:
cùng 500 cái mà 8 người khác hẳn 20 người, định mức 400 khác hẳn định mức 700. `Đạt %` và `Năng suất`
**không có cột** — chúng suy ra được, mà §11 đã chốt _không lưu số tính được_.

---

## 8b. Đóng thùng theo giờ — sổ thứ 15

```sql
CREATE TABLE packing_hourly (
  id       uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  round_id uuid NOT NULL REFERENCES mo_round(id) ON DELETE CASCADE,
  work_date date NOT NULL,
  slot_hour smallint NOT NULL CHECK (slot_hour BETWEEN 0 AND 23),

  boxes       int NOT NULL CHECK (boxes > 0),        -- chỉ đếm THÙNG ĐẦY
  pcs_per_box int NOT NULL CHECK (pcs_per_box > 0),  -- ĐÓNG DẤU quy cách lúc ghi

  note        text,
  recorded_by uuid NOT NULL REFERENCES app_user(id),
  recorded_at timestamptz NOT NULL DEFAULT now(),

  UNIQUE (round_id, work_date, slot_hour)   -- §7b.2 mỗi khung mỗi ngày một lần
);

CREATE INDEX ON packing_hourly (round_id, work_date, slot_hour);
```

**Vì sao đóng dấu `pcs_per_box` vào từng dòng** thay vì đọc sang `manufacturing_order`: cùng lý lẽ với
`target_qty` · `required_sec` ở `mo_round` (§4). Quy cách bị sửa — dù chỉ để vá một lần nhập sai — thì
mọi dòng thùng cũ lập tức quy ra một số pcs khác, và sản lượng tháng trước tự đổi. Đóng dấu là chốt
con số ĐÃ DÙNG lúc đó.

**Chỉ đếm THÙNG ĐẦY** (§7b.2). Thùng lẻ chỉ đóng khi biết chắc không còn hàng nào tới nữa — tức là lúc
`Kết thúc đóng thùng`, và nó vào `packing.qty_packed`, không vào sổ này. Cho ghi thùng lẻ từng giờ thì
phép `boxes × pcs_per_box` hết đúng, mà cả hệ thống dựa vào phép đó.

**Hàng lẻ KHÔNG có cột.** `lẻ = số đã làm ra − Σ(boxes × pcs_per_box)` — suy ra được nên không lưu
(§11). Và nó **không phải** `production.qty_short`: _thiếu_ là chưa làm ra được, phải làm thêm; _lẻ_ là
đã làm ra rồi, chỉ chưa gom đủ một thùng.

> **Tiến độ MO vẫn đọc `packing.qty_packed`, không đọc bảng này.** Sổ này là nhật ký trong ca để thấy
> nhịp đóng thùng và số lẻ đang tồn; con số chốt của vòng vẫn là một dòng `packing` (§5.4). Hai sổ độc
> lập, đối soát nhau — xem `v_packing_reconcile` (§11).

---

## 9. Nhật ký

```sql
CREATE TABLE mo_event (
  id       bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  mo_id    uuid NOT NULL REFERENCES manufacturing_order(id),
  round_id uuid REFERENCES mo_round(id),      -- NULL với tạo lệnh / Submit / huỷ
  step_no  smallint,
  action   text NOT NULL,
  from_state text,
  to_state   text,
  reason_text text,
  actor_id  uuid REFERENCES app_user(id),     -- NULL = hệ thống
  occurred_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX ON mo_event (mo_id, occurred_at DESC);
CREATE INDEX ON mo_event (round_id);
CREATE INDEX ON mo_event (action, occurred_at DESC);

REVOKE UPDATE, DELETE ON mo_event FROM PUBLIC;
CREATE RULE mo_event_no_update AS ON UPDATE TO mo_event DO INSTEAD NOTHING;
CREATE RULE mo_event_no_delete AS ON DELETE TO mo_event DO INSTEAD NOTHING;
```

`round_id` **được phép rỗng**: tạo lệnh, Submit và huỷ lệnh xảy ra trước khi có lượt nào — mà đó lại
đúng là chỗ hay tranh chấp nhất.

---

## 9b. `scan_dedupe` — hạ tầng, KHÔNG thuộc 15 sổ

Đầu đọc mã vạch hay bắn hai lần liền nhau, và người vận hành có thể F5 giữa chừng.
Không chặn thì một lần quét thành hai bước, hoặc một lần bàn giao thành hai dòng.

```sql
CREATE TABLE scan_dedupe (
  mo_id      uuid NOT NULL REFERENCES manufacturing_order(id) ON DELETE CASCADE,
  station_no smallint NOT NULL,
  scanned_at timestamptz NOT NULL DEFAULT now(),
  result_message text NOT NULL DEFAULT '',
  PRIMARY KEY (mo_id, station_no)
);
```

**Khoá chính là (mã, trạm) chứ không phải mã.** Cùng một MO quét tiếp ở trạm kế bên phải ăn ngay —
chỉ chặn khi quét lại ĐÚNG trạm đó trong cửa sổ 2 giây (BRD §1b.3).

**Một dòng cho mỗi cặp, quét lại thì ĐÈ lên** (`ON CONFLICT DO UPDATE`), không đẻ thêm dòng. Bảng này
vì vậy không lớn theo thời gian: tối đa *(số MO đang chạy × 6 trạm)* dòng.

**`result_message` lưu nguyên văn câu trả lời lần trước.** Lần bắn trùng thứ hai nhận lại đúng câu đó
kèm cờ `duplicate: true` — người ở trạm thấy "đã nhận rồi" chứ không thấy báo lỗi, vì họ không làm gì sai.

Vì sao đây **không** phải quyển sổ thứ 16:

| Sổ nghiệp vụ | `scan_dedupe` |
|---|---|
| Trả lời "chuyện gì đã xảy ra với lệnh này" | Trả lời "2 giây trước có ai vừa bắn không" |
| Xoá đi là mất dữ liệu | `TRUNCATE` lúc nào cũng được, chỉ mất chống trùng trong 2 giây |
| Có trong ERD | Không — không mang quan hệ nghiệp vụ nào |

Tương ứng trong code: `app/scan/models.py` · `app/scan/repository.py`.

---

## 9c. `refresh_token` — hạ tầng, KHÔNG thuộc 15 sổ

Đăng nhập một lần, đổi access token nhiều lần trong ca. Bảng này giữ danh sách refresh đã phát để
**thu hồi được** — không có nó thì nút Đăng xuất chỉ là xoá cookie phía máy, ai giữ bản sao vẫn dùng
tiếp tới khi token hết hạn.

```sql
CREATE TABLE refresh_token (
  id          uuid PRIMARY KEY,
  user_id     uuid NOT NULL REFERENCES app_user(id) ON DELETE CASCADE,

  -- Lưu BĂM (sha256), không lưu chuỗi gốc — rò CSDL cũng không dựng lại được token.
  token_hash  text NOT NULL UNIQUE,

  issued_at   timestamptz NOT NULL DEFAULT now(),
  expires_at  timestamptz NOT NULL,

  used_at     timestamptz,   -- rỗng = còn dùng được; có = đã đổi lấy access mới
  revoked_at  timestamptz,   -- rỗng = còn hiệu lực; có = đăng xuất hoặc bị thu hồi cả chuỗi
  replaced_by uuid REFERENCES refresh_token(id),   -- lần ngược cả chuỗi

  CONSTRAINT refresh_expires_after_issued CHECK (expires_at > issued_at)
);

CREATE INDEX ON refresh_token (user_id);
CREATE INDEX refresh_token_con_song
  ON refresh_token (user_id) WHERE revoked_at IS NULL AND used_at IS NULL;
```

**`used_at` là cột quan trọng nhất.** Refresh dùng **đúng một lần** rồi đổi cái mới. Thấy một token đã
`used_at` mà lại được gửi lên lần nữa nghĩa là **có người giữ bản sao** — không biết bản sao ở máy nào,
nên thu hồi CẢ CHUỖI của người đó và bắt đăng nhập lại.

Vì sao không phải quyển sổ thứ 16: cùng lý lẽ với `scan_dedupe` (§9b) — nó trả lời *"phiên đăng nhập
này còn hiệu lực không"*, không trả lời *"chuyện gì đã xảy ra với lệnh sản xuất"*. Xoá sạch bảng thì chỉ
mất các phiên đang mở, không mất dữ liệu sản xuất nào.

Tương ứng trong code: `app/modules/auth/models.py` · `app/modules/auth/service.py`.

---

## 10. Trigger — luật `CHECK` không với tới

`CHECK` chỉ nhìn được một dòng của một bảng. Bốn luật sau phải đọc sang bảng khác.

### 10.1 Ba số cộng đúng bằng mục tiêu vòng (§7.5)

```sql
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
```

**Bằng đúng, không phải nhỏ hơn hoặc bằng.** Mỗi PCS giao xuống chuyền phải rơi vào đúng một trong ba
nhóm; tổng lệch nghĩa là có hàng không ai khai.

### 10.2 Đóng thùng không vượt SL đạt (§7b)

```sql
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
```

### 10.3 Khoá cứng MO sau Submit (§4A)

```sql
CREATE OR REPLACE FUNCTION mo_lock_after_submit() RETURNS trigger AS $$
BEGIN
  IF OLD.status <> 'DRAFT' AND (
       NEW.code, NEW.product_name, NEW.quantity, NEW.required_production_sec, NEW.pcs_per_box)
    IS DISTINCT FROM (
       OLD.code, OLD.product_name, OLD.quantity, OLD.required_production_sec, OLD.pcs_per_box) THEN
    RAISE EXCEPTION 'MO % đã Submit — không sửa được. Huỷ rồi tạo lệnh mới (§4A)', OLD.code;
  END IF;
  RETURN NEW;
END $$ LANGUAGE plpgsql;

CREATE TRIGGER trg_mo_lock BEFORE UPDATE ON manufacturing_order
  FOR EACH ROW EXECUTE FUNCTION mo_lock_after_submit();
```

### 10.4 Tổng sản lượng giờ không vượt mục tiêu vòng (§7.2b)

```sql
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
```

### 10.5 Không đóng nhiều hơn số đã làm ra (§7b.2)

```sql
CREATE OR REPLACE FUNCTION packing_hourly_within_made() RETURNS trigger AS $$
DECLARE lam_ra int; da_dong int;
BEGIN
  -- Chốt sổ SX rồi thì lấy SL đạt; chưa thì tạm lấy Σ sản lượng giờ.
  SELECT qty_ok INTO lam_ra FROM production WHERE round_id = NEW.round_id;
  IF lam_ra IS NULL THEN
    SELECT COALESCE(SUM(qty), 0) INTO lam_ra FROM hourly_output WHERE round_id = NEW.round_id;
  END IF;

  SELECT COALESCE(SUM(boxes * pcs_per_box), 0) INTO da_dong
    FROM packing_hourly WHERE round_id = NEW.round_id AND id <> NEW.id;

  IF da_dong + NEW.boxes * NEW.pcs_per_box > lam_ra THEN
    RAISE EXCEPTION 'Đóng % pcs vượt số đã làm ra của vòng (%)',
      da_dong + NEW.boxes * NEW.pcs_per_box, lam_ra;
  END IF;
  RETURN NEW;
END $$ LANGUAGE plpgsql;

CREATE TRIGGER trg_packing_hourly_cap BEFORE INSERT OR UPDATE ON packing_hourly
  FOR EACH ROW EXECUTE FUNCTION packing_hourly_within_made();
```

Không đóng được cái chưa làm ra. Đây là chỗ hai sổ độc lập — sản lượng giờ và thùng giờ — gặp nhau.

---

## 11. View — mọi con số dẫn xuất

**Không lưu số tính được.** Lưu thì phải có trigger giữ đồng bộ, và lệch lúc nào không ai biết.

```sql
-- Thời gian từng bước của từng lượt — nền cho cả hai cách đọc
CREATE VIEW v_step_time AS
SELECT s.round_id, r.mo_id, r.round_no, s.step_no,
       EXTRACT(EPOCH FROM (COALESCE(s.closed_at, now()) - s.accepted_at))::int AS sec
FROM mo_step s
JOIN mo_round r ON r.id = s.round_id;

-- Cộng dồn một bước qua MỌI LƯỢT của một đơn — con số hiện ở bảng Timer
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

-- Tiến độ MO: cộng dồn qua các vòng.
-- qty_done tính theo SL ĐÃ ĐÓNG THÙNG (BRD §6b.2), KHÔNG theo SL đạt của Sản xuất:
-- hàng đạt mà chưa đóng thùng thì chưa giao được, chưa tính vào tiến độ.
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

-- Một dòng cho Bảng đang chạy (§7.2) — gom mọi thứ màn hình cần
CREATE VIEW v_round_board AS
SELECT r.id AS round_id, m.code, m.product_name, m.quantity,
       r.round_no, r.target_qty, r.required_sec,
       k.actual_sec, k.on_time, k.late_sec,
       p.qty_ok, p.qty_ng, p.qty_short, p.closed_at AS production_closed_at,
       pk.qty_packed, pk.completed_at AS packing_done_at
FROM mo_round r
JOIN manufacturing_order m ON m.id = r.mo_id
LEFT JOIN v_round_kpi k  ON k.round_id  = r.id
LEFT JOIN production  p  ON p.round_id  = r.id
LEFT JOIN packing     pk ON pk.round_id = r.id
WHERE r.closed_at IS NULL;

-- Đối soát sản lượng giờ với SL đạt (§7.2b)
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

-- Đối soát thùng với số đã làm ra, và HÀNG LẺ đang tồn (§7b.2)
-- `le_pcs` chính là con số panel hiện thường trực. Nó KHÔNG phải `qty_short`.
CREATE VIEW v_packing_reconcile AS
SELECT r.id AS round_id, r.mo_id, r.round_no,
       COALESCE(SUM(ph.boxes), 0)                      AS boxes_total,
       COALESCE(SUM(ph.boxes * ph.pcs_per_box), 0)     AS packed_pcs,
       COALESCE(p.qty_ok, h.hourly_total, 0)           AS made_pcs,
       GREATEST(0, COALESCE(p.qty_ok, h.hourly_total, 0)
                   - COALESCE(SUM(ph.boxes * ph.pcs_per_box), 0)) AS le_pcs
FROM mo_round r
LEFT JOIN packing_hourly ph ON ph.round_id = r.id
LEFT JOIN production     p  ON p.round_id  = r.id
LEFT JOIN (SELECT round_id, SUM(qty) AS hourly_total FROM hourly_output GROUP BY round_id) h
       ON h.round_id = r.id
GROUP BY r.id, p.qty_ok, h.hourly_total;
```

> **Màn hình nào cũng đọc view, không đọc thẳng bảng.** Tách bảng làm câu truy vấn dài hơn — `v_round_board`
> gánh phần đó một lần, ứng dụng vẫn đọc một dòng như cũ.

---

## 12. Đối chiếu BRD → ràng buộc

| Luật trong BRD | Đứng ở đâu |
|---|---|
| §2.2 mã `M` + 6 chữ số | `CHECK (code ~ '^M[0-9]{6}$')` |
| §2.3 huỷ lệnh kèm lý do | `mo_cancel_needs_reason` |
| §4A khoá cứng sau Submit | trigger `mo_lock_after_submit` |
| §3 bàn giao là bước duy nhất ở Kho | có dòng `warehouse_out` = đã bàn giao |
| §5 QC FAIL cần lý do | `qc_fail_needs_reason` *(trong `qc_result`)* |
| §6b mỗi đơn một lượt đang mở | chỉ mục `mo_round_one_open` |
| §6b.2 · §7.3 mục tiêu và hạn mức theo vòng | `target_qty` · `required_sec` `NOT NULL` lúc `INSERT` |
| §7.5 ba số cộng bằng mục tiêu | trigger `production_balances` |
| §7.5 hai lý do riêng | `ng_needs_reason` · `short_needs_reason` |
| §7.5 chốt sổ một lần | `RULE production_no_update` |
| §7b đóng thùng không vượt SL đạt | trigger `packing_within_ok` |
| §11B thời gian chờ | đoạn `WAIT` → `v_line_time.wait_sec` |
| §9 Timer cộng dồn qua mọi lượt | `v_step_total` |
| §6b.2 tiến độ tính theo SL đã đóng thùng | `v_mo_progress.qty_done` = `SUM(packing.qty_packed)` |
| §9b phân quyền 13 vai | `app_user.roles` — kiểm ở tầng ứng dụng, chưa `GRANT` theo bảng |
| §12B vượt vẫn đếm tiếp | view dùng `COALESCE(ended_at, now())` |
| §14B một chuyền nhiều MO | **không** unique trên `line_id` |
| §15A ba trạng thái của chuyền | `segment_kind` + đoạn đang mở |
| §16 hoàn thành đồng bộ | tầng ứng dụng: đóng mọi đoạn của vòng cùng **một** `clock_timestamp()` |
| §17 dừng bắt buộc lý do | `seg_reason_only_on_wait` + kiểm ở ứng dụng |
| §21A chuyền chậm nhất | `MAX(run_sec)` trong `v_round_kpi` |
| §7.2b chặn trùng khung giờ | `UNIQUE (round_id, work_date, slot_hour)` |
| §7.2b chặn vượt mục tiêu | trigger `hourly_within_target` |
| §7.2b ba số mỗi khung giờ | `hourly_output.headcount` · `target_qty` · `qty` |
| §7b.2 quy cách pcs/thùng | `manufacturing_order.pcs_per_box`, khoá cứng bởi `mo_lock_after_submit` |
| §7b.2 đếm thùng theo giờ | sổ `packing_hourly`, `UNIQUE (round_id, work_date, slot_hour)` |
| §7b.2 không đóng nhiều hơn số làm ra | trigger `packing_hourly_within_made` |
| §7b.2 hàng lẻ ≠ SL thiếu | `v_packing_reconcile.le_pcs` — **suy ra**, không có cột |
| §7b.2 thùng cuối được đóng thiếu | **không có ràng buộc nào** — `packing.qty_packed` nhận pcs, không nhận thùng |
| §25A nhật ký append-only | `REVOKE` + hai `RULE` |
| — một chuyền không chạy hai MO cùng lúc | `line_run_no_overlap` |

---

## 13. Thêm một trạm về sau — đúng ba việc

Giả sử khách yêu cầu **kiểm kích thước** trước khi nhập kho:

```sql
-- 1. Nới số bước
ALTER TABLE mo_step DROP CONSTRAINT mo_step_step_no_check;
ALTER TABLE mo_step ADD  CONSTRAINT mo_step_step_no_check CHECK (step_no BETWEEN 0 AND 6);

-- 2. Sổ riêng cho trạm mới — KHÔNG đụng bảng nào đang có dữ liệu
CREATE TABLE dimension_check (
  round_id    uuid PRIMARY KEY REFERENCES mo_round(id) ON DELETE CASCADE,
  checked_at  timestamptz NOT NULL DEFAULT now(),
  checked_by  uuid NOT NULL REFERENCES app_user(id),
  result      qc_verdict NOT NULL,
  sample_qty  int NOT NULL CHECK (sample_qty > 0),
  defect_qty  int NOT NULL CHECK (defect_qty >= 0),
  reason_text text,
  CHECK (result <> 'FAIL' OR reason_text IS NOT NULL),
  CHECK (defect_qty <= sample_qty)
);

-- 3. Thêm cột vào view của màn hình cần
CREATE OR REPLACE VIEW v_round_board AS SELECT … LEFT JOIN dimension_check d ON …;
```

**Lượt chạy cũ không có dòng trong bảng mới** — và đó chính là câu trả lời đúng: *"lượt đó chạy từ thời
chưa có trạm này"*. Nếu đắp cột vào bảng chính thì mọi lượt cũ mọc thêm ô rỗng vĩnh viễn, không phân
biệt được *"chưa kiểm"* với *"thời đó không có trạm"*.

---

## 14. Việc tiếp theo

| Việc | Ghi chú |
|---|---|
| Dữ liệu mẫu: 14 chuyền + danh mục lý do | cần trước khi chạy thử |
| Hàm `accept_step()` — đóng bước trước, mở bước sau, ghi nhật ký | một giao dịch, tránh nửa vời |
| Hàm `close_round()` — chốt vòng, quyết định COMPLETED hay mở vòng mới | một giao dịch |
| Phân quyền theo bảng trạm | **#26 đã chốt** (BRD §9b). Code hiện còn 7 vai phẳng, cần đổi sang 13 vai |
| Chỉ mục cho màn hình điều hành | đo rồi mới thêm, đừng đoán |
| ~~Migration `0006`~~ — `pcs_per_box` · `headcount` · `target_qty` · sổ `packing_hourly` | **XONG** 2026-09-15. Ba cột mới đều NULL được hoặc có DEFAULT nên không phải vá dữ liệu cũ; `downgrade()` đã thử lùi rồi tiến lại |

> **10 câu hỏi mở** còn lại ở §10 BRD (#26 đã chốt ngày 2026-09-14, xem §9b BRD).
> Cái còn chạm thẳng vào thiết kế là **#38** — bỏ ô nhập SL ở Đóng thùng. Bỏ được thì `qty_packed` thành
> cột tính từ `production.qty_ok`, bớt một ô nhập và một trigger. Nhưng phải chốt trước khi xưởng chạy
> thật: đổi sau là phải vá dữ liệu đã có.
