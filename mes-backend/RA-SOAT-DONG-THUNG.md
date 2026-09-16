# Rà soát — Đếm THÙNG + ba số mỗi khung giờ

> Phạm vi: mọi thay đổi ở `mes-backend/` cho **BRD v2.21 → v2.23** và **DB-GON v2.7 → v2.9**.
> Ngày: 2026-09-15 · Migration: `0005` (đổi tên) và `0006` (đếm thùng)
> Trạng thái lúc viết: **166 passed · 1 skipped** · `./run.sh lint` sạch · `./run.sh docs-check` sạch

Tài liệu này để **đọc đối chiếu với code**, không phải để học lại nghiệp vụ. Nghiệp vụ nằm ở
`demo/BRD-v2-chot.md` §7.2b + §7b.2; thiết kế CSDL ở `demo/DB-GON.md` §3 · §8 · §8b · §10.5 · §11.

---

## 0. Ba câu hỏi để rà nhanh

Nếu chỉ có 10 phút, kiểm đúng ba chỗ này — ba chỗ còn lại đều suy ra từ chúng:

| # | Câu hỏi | Kiểm ở đâu |
| - | --- | --- |
| 1 | Tiến độ MO có bao giờ tính bằng THÙNG không? | [warehouse_in/service.py](app/modules/warehouse_in/service.py) — phải **không có** chữ `box` nào |
| 2 | Quy cách có bị đọc lại lúc báo cáo không? | [packing_hourly.pcs_per_box](app/modules/packing/models.py#L34) — phải đóng dấu vào từng dòng |
| 3 | "Hàng lẻ" có bị lưu thành cột không? | Phải **không có** cột nào tên `le`/`remainder` — nó là số suy ra |

Ba câu này chính là ba chỗ dễ làm sai nhất, và cả ba đều có bài kiểm giữ (§5).

---

## 1. Hai luật quyết định cả thiết kế

Đọc trước khi rà code, vì mọi lựa chọn dưới đây đều bắt nguồn từ hai câu này:

**Luật 1 — PCS là đơn vị gốc, THÙNG chỉ là cách đếm.**
Mọi ràng buộc sẵn có chạy bằng pcs (`đạt + hỏng + thiếu = mục tiêu vòng`, cộng dồn ở Nhập kho).
Đưa một đơn vị thô — bội số của quy cách — vào giữa dây số học đó là chỗ sinh ra lỗi, vì đơn hàng
hiếm khi chia hết cho quy cách.

**Luật 2 — Thùng CUỐI của đơn được đóng thiếu.**
`3.000 ÷ 800 = 3 thùng đầy + 1 thùng lẻ 600`. Đây là **mặc định, không phải ngoại lệ**.

> Hệ quả quan trọng nhất: **hàng lẻ KHÔNG phải hàng thiếu.**
> _Thiếu_ = chưa làm ra được → phải làm thêm → mở vòng mới.
> _Lẻ_ = đã làm ra rồi, chỉ chưa gom đủ một thùng → **không phải làm gì cả**.
>
> Vì Luật 2, cuối vòng không bao giờ còn hàng lẻ bị bỏ lại — nên **logic vòng chạy (§6b, §8)
> không phải sửa một dòng nào.** Nếu anh thấy tôi có đụng vào `round/` hay `warehouse_in/`, đó là
> lỗi, báo tôi.

---

## 2. Migration — cái duy nhất chạm vào dữ liệu thật

### `0005_doi_ten_tram.py` — đổi tên hiển thị

Đổi tên **chỉ ở chữ hiển thị**: `Bàn chờ → Bàn team leader`, `Đóng gói → Đóng thùng`.

| Rà cái gì | Vì sao |
| --- | --- |
| Tên kỹ thuật **không** đổi: `WAITING_MEMBER` · `RETURN_BANCHO` · `PACK_START` · bảng `packing` · cột `qty_packed` | Đổi mã hành động là **phá `mo_event`** — sổ đó chặn UPDATE/DELETE bằng RULE, dòng cũ và mới sẽ không nối được |
| Không sửa file `0001`/`0002`/`0004` | Migration đã chạy là lịch sử. Sửa file cũ thì máy đã nâng cấp rồi chẳng có tác dụng, mà lại làm hai máy lệch nhau |
| Tìm theo `emp_code`, không theo `full_name` | Mã nhân viên là khoá thật; tên có thể đã bị sửa tay |

### `0006_dong_thung.py` — đếm thùng

[app/db/migrations/versions/0006_dong_thung.py](app/db/migrations/versions/0006_dong_thung.py)

| Thêm gì | Ràng buộc | Điểm cần soi |
| --- | --- | --- |
| `manufacturing_order.pcs_per_box` | `NOT NULL DEFAULT 0 CHECK (>= 0)` | **0 có nghĩa THẬT**: mặt hàng không đóng thùng. Không phải "chưa biết" |
| `hourly_output.headcount` · `target_qty` | `NULL được`, `CHECK (> 0)` | Dòng ghi trước `0006` không có hai số đó. Điền 0 vào là **bịa ra năng suất chưa ai đo** |
| bảng `packing_hourly` | `UNIQUE (round_id, work_date, slot_hour)` | Sổ thứ 15 |
| trigger `packing_hourly_within_made` | — | Không đóng nhiều hơn số đã làm ra |
| view `v_packing_reconcile` | — | `le_pcs` — hàng lẻ, **suy ra chứ không lưu** |
| sửa `mo_lock_after_submit` | — | Thêm `pcs_per_box` vào khoá cứng §4A |

**Ba điểm dễ bỏ sót khi rà migration này:**

1. **Câu lỗi của trigger bắt đầu bằng `'Đã đóng '`, không phải `'Đóng '`.**
   [errors.py](app/common/errors.py#L93) dịch lỗi trigger bằng `startswith`, mà `'Đóng '` đã thuộc về
   `packing_within_ok`. Trùng tiền tố thì hai lỗi khác nhau ra cùng một mã.
2. **Ba cột mới đều NULL được hoặc có DEFAULT.** Đó là điều kiện để chạy trên CSDL đang có hàng thật
   mà không phải vá dữ liệu và không khoá bảng lâu.
3. **Có `downgrade()` và tôi đã thử.** `0006 → 0005 → 0006`, `packing_hourly` biến mất rồi hiện lại.

---

## 3. Code — từng tệp, từng chỗ

### 3.1 Quy cách đi suốt từ API xuống CSDL

| Tệp | Dòng | Đổi gì |
| --- | --- | --- |
| [mo/models.py](app/modules/mo/models.py#L33) | 33 | `pcs_per_box: Mapped[int]`, default 0 |
| [mo/schemas.py](app/modules/mo/schemas.py#L15) | 15 · 35 | `MoCreateIn.pcs_per_box` (ge=0, default 0) · `MoOut.pcs_per_box` |
| [mo/service.py](app/modules/mo/service.py#L41) | 41 · 78 | `NewMo.pcs_per_box = 0` · `parse_csv` nhận **cột 5 tuỳ chọn** |
| [mo/repository.py](app/modules/mo/repository.py#L21) | 21 | `save_mo(..., pcs_per_box)` |
| [mo/router.py](app/modules/mo/router.py#L34) | 34 | truyền xuống `NewMo` |

> **Cột 5 của CSV phải TUỲ CHỌN.** Nó thêm sau, nên file CSV cũ của xưởng vẫn phải nhập được — thiếu
> cột thì quy cách là 0 = mặt hàng không đóng thùng. Rà chỗ này kỹ: bắt buộc cột 5 là làm gãy quy
> trình nhập hàng loạt đang chạy.

### 3.2 Ba số mỗi khung giờ

| Tệp | Dòng | Đổi gì |
| --- | --- | --- |
| [production/models.py](app/modules/production/models.py#L60) | 60 | `headcount` · `target_qty` — **`int \| None`**, khớp NULL của DB |
| [production/schemas.py](app/modules/production/schemas.py#L51) | 51 | `HourlyIn` — cả ba **bắt buộc** ở API |
| [production/hourly_service.py](app/modules/production/hourly_service.py#L27) | 27 | kiểm `headcount > 0` · `target_qty > 0` |
| [production/repository.py](app/modules/production/repository.py#L126) | 126 | `add_hourly(..., headcount, target_qty)` |
| [production/router.py](app/modules/production/router.py#L82) | 82 | truyền ba số, message nói cả ba |

> **Schema bắt buộc nhưng cột thì NULL được — đó là CỐ Ý.** API mới phải đủ ba số; dòng cũ trong CSDL
> thì không có, và không được phép đoán. Hai chỗ khác nhau là đúng, đừng "sửa cho đồng bộ".

> **`Đạt %` và `Năng suất` KHÔNG có ở đâu cả trong backend.** Chúng suy ra từ ba số trên. Cho nhập tay
> là mở đường cho số liệu tự mâu thuẫn — và người ta sẽ điền số đẹp chứ không điền số thật.

### 3.3 Đếm thùng — phần mới hoàn toàn

| Tệp | Dòng | Là gì |
| --- | --- | --- |
| [packing/models.py](app/modules/packing/models.py#L34) | 34 | `PackingHourly` |
| [packing/schemas.py](app/modules/packing/schemas.py#L22) | 22 · 39 | `PackingHourlyIn` · `PackingHourlyOut` |
| [packing/repository.py](app/modules/packing/repository.py#L43) | 43 · 69 | `add_packing_hourly` · `packed_boxes_pcs` |
| [packing/hourly_service.py](app/modules/packing/hourly_service.py#L57) | 43 · 57 | `_made_pcs` · `add_packing_hourly` — **tệp mới** |
| [packing/router.py](app/modules/packing/router.py#L38) | 38 | `POST /packing/{code}/hourly` |

**Bốn chỗ tôi muốn anh soi kỹ:**

1. **`pcs_per_box` chép vào từng dòng** ([models.py:34](app/modules/packing/models.py#L34)).
   Không đọc sang `manufacturing_order` lúc báo cáo. Cùng lý lẽ với `mo_round.target_qty`: sửa quy
   cách một lần là mọi dòng cũ quy ra số pcs khác, sản lượng tháng trước tự đổi.

2. **`_made_pcs` KHÔNG lấy mục tiêu vòng** ([hourly_service.py:43](app/modules/packing/hourly_service.py#L43)).
   Chốt sổ rồi thì `production.qty_ok`, chưa thì Σ sản lượng giờ. Mục tiêu là số **phải** làm, không
   phải số **đã** làm — lấy nhầm là cho phép đóng thùng hàng chưa tồn tại.

3. **Chỉ đếm THÙNG ĐẦY.** Thùng lẻ chỉ đóng lúc `POST /packing/{code}/finish` và vào `qty_packed`.
   Cho ghi thùng lẻ từng giờ thì phép `boxes × pcs_per_box` hết đúng — mà cả hệ thống dựa vào đó.

4. **Hai lớp chặn nằm ở CSDL, không ở service** — UNIQUE chặn ghi trùng, trigger chặn đóng quá.
   Để ở đó thì đúng cả khi có người ghi thẳng vào CSDL.

### 3.4 Vốn từ và dịch lỗi

| Tệp | Dòng | Thêm gì |
| --- | --- | --- |
| [vocab/error_codes.py](app/common/vocab/error_codes.py#L100) | 100 · 113 | `HOURLY_PEOPLE` · `HOURLY_TARGET` · `NO_PCS_PER_BOX` · `BOX_DUP` · `BOX_OVER_MADE` |
| [vocab/action_codes.py](app/common/vocab/action_codes.py#L70) | 70 | `PACK_HOURLY` |
| [errors.py](app/common/errors.py#L77) | 77 · 93 | ánh xạ `packing_hourly_..._key` → `BOX_DUP` · tiền tố `"Đã đóng "` → `BOX_OVER_MADE` |

---

## 4. API — hợp đồng với FE

```
POST /v1/mos                     + pcs_per_box                    (CSV: cột 5 tuỳ chọn)
POST /v1/hourly/{code}           + headcount, target_qty          → ba số, cả ba bắt buộc
POST /v1/packing/{code}/hourly   MỚI — ghi số thùng đầy
```

`POST /v1/packing/{code}/hourly` trả về:

```json
{ "boxes": 1, "pcs_per_box": 800, "packed_pcs": 1600,
  "made_pcs": 1800, "le_pcs": 200, "message": "…còn lẻ 200 trên bàn…" }
```

> Trả thẳng `le_pcs` để màn hình khỏi tự tính lại — hai nơi tính là hai nơi lệch. Và câu `message`
> nói rõ *"chưa đủ thùng, KHÔNG phải hàng thiếu"*, vì đó chính là chỗ người vận hành hay hiểu nhầm.

**Năm mã lỗi mới FE cần biết:**

| Mã | HTTP | Khi nào |
| --- | --- | --- |
| `NO_PCS_PER_BOX` | 409 | MO chưa khai quy cách mà đòi đếm thùng |
| `BOX_DUP` | 409 | Khung giờ đó của ngày đó ghi thùng rồi |
| `BOX_OVER_MADE` | 409 | Đóng nhiều hơn số đã làm ra |
| `HOURLY_PEOPLE` | 422 | Thiếu số người |
| `HOURLY_TARGET` | 422 | Thiếu sản lượng yêu cầu |

---

## 5. Bài kiểm — đọc để biết luật nào đang được giữ

[tests/test_dong_thung.py](tests/test_dong_thung.py) — 10 bài. Cột cuối là **luật bị phá nếu bài đó đỏ**:

| Dòng | Bài | Giữ luật gì |
| --- | --- | --- |
| [47](tests/test_dong_thung.py#L47) | `quy_cach_luu_va_khoa_cung_sau_submit` | §4A — quy cách khoá cứng như `quantity` |
| [61](tests/test_dong_thung.py#L61) | `khong_khai_quy_cach_thi_khong_dem_thung_duoc` | Không có cầu nối thì không quy đổi |
| [73](tests/test_dong_thung.py#L73) | `ba_so_moi_khung_gio_xuong_toi_CSDL` | Ba số xuống tới cột thật |
| [85](tests/test_dong_thung.py#L85) | `vuot_san_luong_yeu_cau_cua_MOT_khung_thi_KHONG_chan` | **`Đạt 117%` là tin tốt**, không phải lỗi |
| [94](tests/test_dong_thung.py#L94) | `thieu_so_nguoi_hoac_san_luong_yeu_cau_thi_chan` | Cả ba bắt buộc |
| [107](tests/test_dong_thung.py#L107) | `hang_le_khong_bien_mat_va_khong_phai_hang_thieu` | **Kịch bản gốc của anh** — xem dưới |
| [130](tests/test_dong_thung.py#L130) | `thung_cuoi_duoc_dong_thieu_nen_don_xong_trong_MOT_vong` | **Luật 2** — không có nó là kẹt vòng vô hạn |
| [153](tests/test_dong_thung.py#L153) | `khong_dong_duoc_nhieu_hon_so_da_lam_ra` | Trigger `packing_hourly_within_made` |
| [170](tests/test_dong_thung.py#L170) | `trung_khung_gio_thi_chan` | UNIQUE (vòng, ngày, khung) |
| [183](tests/test_dong_thung.py#L183) | `quy_cach_DONG_DAU_vao_tung_dong` | Quy cách nằm trên dòng, không tra sang MO |

Bài [107](tests/test_dong_thung.py#L107) chạy đúng ca anh nêu:

```
giờ 1: làm  800 · đóng 1 thùng → đã đóng  800 · lẻ   0
giờ 2: làm 1000 · đóng 1 thùng → đã đóng 1600 · lẻ 200   ← 200 lẻ HIỆN RA, không mất
giờ 3: làm 1200 · đóng 1 thùng → đã đóng 2400 · lẻ 600
chốt 3.000 pcs (gồm thùng lẻ) → COMPLETED ngay VÒNG 1
```

[tests/conftest.py](tests/conftest.py#L180) thêm ba helper: `make_mo(box=…)` · `flow.hourly(...)` ·
`flow.pack_hourly(...)` · `flow.pack_start(...)`.

---

## 6. Ba lỗi đã gặp — ghi lại vì chúng sẽ cắn lại người sau

| Lỗi | Vì sao | Nằm ở đâu |
| --- | --- | --- |
| Trigger ném `ProgrammingError`, **không** `IntegrityError` | `RAISE EXCEPTION` của plpgsql là ProgrammingError; chỉ ràng buộc UNIQUE mới ném IntegrityError. `translate_db_error` nhận cả hai | [test_dong_thung.py:153](tests/test_dong_thung.py#L153) có chú thích |
| Chạy **riêng** một file test thì mapper gãy | `mo/models.py` khai quan hệ `rounds` bằng tên chuỗi `"MoRound"`; chạy cả bộ thì file khác nạp hộ, chạy riêng thì không ai nạp | [test_dong_thung.py:28-31](tests/test_dong_thung.py#L28-L31) |
| MO `COMPLETED` rồi thì **không còn vòng mở** để đọc | `flow.round_of()` ném `NotFound`. Đọc `out.new_round_no is None` thay vì đọc vòng | [test_dong_thung.py:130](tests/test_dong_thung.py#L130) |

---

## 7. Cái tôi KHÔNG làm — để anh biết mà không phải đi tìm

| Việc | Vì sao chưa |
| --- | --- |
| `GET` đọc lại sổ thùng theo vòng | Chưa có màn hình nào cần. `packing_hourly_of` đã có sẵn ở repository, thêm route là xong |
| Đưa `le_pcs` vào màn Truy vết (`board/service.py`) | BRD chưa nói bảng truy vết phải hiện số lẻ. Thêm bừa là đoán yêu cầu |
| Dùng view `v_packing_reconcile` trong code | Code đang tự cộng bằng `packed_boxes_pcs`. View tồn tại cho báo cáo/SQL tay. **Hai đường tính cùng một số** — đây là món nợ, xem dưới |
| Ràng buộc `qty_packed` phải chia hết cho quy cách | Cố ý **không** — Luật 2 nói thùng cuối được đóng thiếu |
| `pyright` | `pyrightconfig.json` có sẵn nhưng chưa có `./run.sh types`. Vẫn còn vài chỗ kiểu khai rộng hơn sự thật |

> **Món nợ đáng nhớ nhất:** `le_pcs` đang được tính ở **hai nơi** — Python trong
> [hourly_service.py](app/modules/packing/hourly_service.py#L57) và SQL trong view
> `v_packing_reconcile`. Hôm nay hai bên ra cùng một số, nhưng đó là thứ sẽ lệch âm thầm. Khi nào có
> màn hình đọc view, nên bỏ phép tính Python và đọc view cho cả hai đường.

---

## 8. Chạy lại để tự kiểm

```bash
cd mes-backend
./run.sh mig                  # lên 0006
./run.sh lint                 # phải sạch
./run.sh test                 # 166 passed · 1 skipped
./run.sh docs-check           # link tài liệu còn trỏ đúng dòng

# chỉ phần đếm thùng
.venv/Scripts/python.exe -m pytest tests/test_dong_thung.py -q

# đối chiếu lược đồ thật
./run.sh sql "SELECT column_name, is_nullable FROM information_schema.columns
              WHERE table_name='packing_hourly' ORDER BY ordinal_position;"
```
