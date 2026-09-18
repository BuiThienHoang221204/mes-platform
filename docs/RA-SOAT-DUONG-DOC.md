# Rà soát — mọi đường ĐỌC dữ liệu

Bản kiểm đếm **sinh từ mã nguồn đang chạy**, không gõ tay: duyệt `app.routes` để lấy
endpoint, và phân tích cú pháp từng `repository.py` để phân loại hàm đọc / hàm ghi.

```
41 endpoint          18 GET  ·  23 POST/DELETE
64 hàm repository    47 đọc  ·  14 ghi  ·  3 không chạm CSDL
 8 view  ·  18 bảng
```

---

## 1 · Endpoint GET

### 1.1 Mười hai đường nghiệp vụ

| Đường dẫn | Module | Gác quyền | Cache | Trả về |
|---|---|---|---|---|
| `GET /board/running` | board | **không** | có | Bảng lệnh đang chạy, mỗi vòng đang mở một dòng + KPI thời gian |
| `GET /board/counts` | board | **không** | có | Số lệnh chờ nhận và đang giữ của cả sáu trạm |
| `GET /board/queue/{station}` | board | `require_step` | có | Hàng chờ một trạm |
| `GET /board/at/{station}` | board | `require_step` | có | Lệnh đang trong tay một trạm |
| `GET /mos` | mo | `require_step` | — | Danh sách lệnh, lọc theo `status` |
| `GET /mos/{code}` | mo | `require_step` | — | Một lệnh |
| `GET /mos/{code}/trace` | board | `require_step` | — | Truy vết: mọi vòng, từng bước, năng suất chuyền, sản lượng giờ |
| `GET /mos/{code}/events` | board | `require_step` | — | Một trang nhật ký (`limit`, `offset`) |
| `GET /lines` | catalog | **không** | — | 14 chuyền, kể cả chuyền đã tắt |
| `GET /reasons` | catalog | **không** | — | Danh mục mã lý do, lọc theo `group` |
| `GET /reports/mo-progress` | reports | **không** | có | Tiến độ từng lệnh |
| `GET /reports/hourly` | reports | **không** | có | Sản lượng giờ đã gộp khung |

### 1.2 Sáu đường hạ tầng

`GET /healthz` · `GET /readyz` · `GET /openapi.json` · `GET /docs` ·
`GET /docs/oauth2-redirect` · `GET /redoc`

### 1.3 Sáu đường KHÔNG gác quyền — cố ý

`/board/running` · `/board/counts` · `/lines` · `/reasons` ·
`/reports/mo-progress` · `/reports/hourly`

Cả sáu đều khai trong danh sách `CO_Y_MO` của `tests/test_permissions.py` **kèm lý do
viết ra chữ**. Test cuối file đó duyệt toàn bộ `app.routes` và bắt mọi endpoint phải
chứa `require_step` / `require_role` / `require_station`, trừ những đường có tên trong
danh sách. Thêm endpoint mà quên gắn quyền là test đỏ ngay — quyết định "mở" ở đây
không sống bằng trí nhớ.

Bốn đường `board` và `reports` mở theo **BRD §9b.5**: màn tổng quan nằm ngoài phạm vi
xem theo trạm của §12.4, vì chúng chỉ có số cộng dồn cả xưởng, không có hàng đợi hay
danh sách lệnh của riêng trạm nào. Hai đường `catalog` là danh mục chỉ đọc.

### 1.4 Sáu trong mười hai đường đi qua `read_cache`

Có cache: bốn đường `/board/*` và hai đường `/reports/*`.

Không cache: `/mos`, `/mos/{code}`, `/mos/{code}/trace`, `/mos/{code}/events`,
`/lines`, `/reasons`.

Cache bám **phiên bản** chứ không chỉ TTL: mỗi thao tác ghi gọi `bump()` và mọi mục
mang phiên bản cũ thành vô hiệu ngay. TTL 5 giây chỉ là lưới an toàn cho trường hợp
có người ghi thẳng vào CSDL không qua service.

---

## 2 · Hàm đọc CSDL — theo module

`ĐỌC` = chỉ truy vấn · `GHI` = có `db.add` / `INSERT` / `UPDATE` / `DELETE` ·
`ĐỌC+GHI` = cả hai.

### auth/repository.py

| Hàm | Loại | Chạm |
|---|---|---|
| `get_user_by_emp_code` | ĐỌC | `app_user` |
| `get_user_by_id` | ĐỌC | `app_user` |
| `find_refresh` | ĐỌC | `refresh_token` — **có khoá dòng** |
| `save_refresh` | GHI | `refresh_token` |
| `revoke_all_for_user` | GHI | `refresh_token` |

### board/repository.py

| Hàm | Loại | Chạm |
|---|---|---|
| `running_rows` | ĐỌC | `v_round_board` |
| `queue_rows` | ĐỌC | `QUEUE_SQL` — sáu câu, mỗi trạm một câu |
| `at_station_rows` | ĐỌC | `mo_step`, `mo_round`, `manufacturing_order`, `app_user`, `warehouse_out`, `packing`, `qc_result` |
| `queue_counts` | ĐỌC | `mo_step`, `mo_round` — **một câu cho cả sáu trạm** |
| `line_rows_of_rounds` | ĐỌC | `v_line_time`, `line` — theo LÔ vòng |
| `step_totals` | ĐỌC | `v_step_total` |
| `mo_progress` | ĐỌC | `v_mo_progress` |

`QUEUE_SQL` là **nguồn duy nhất** của hàng chờ: cả danh sách (`queue_rows`) lẫn con số
trên badge (`queue_counts`) đều dựng từ nó. Viết câu đếm riêng thì sớm muộn hai câu
trôi khỏi nhau, badge hiện một số mà bấm vào ra số khác — không ai báo lỗi.

### catalog/repository.py

| Hàm | Loại | Chạm |
|---|---|---|
| `get_line` | ĐỌC | `line` |
| `list_lines` | ĐỌC | `line` |
| `list_reasons` | ĐỌC | `reason_code` |
| `create_line` | ĐỌC+GHI | `line` — đọc để tự tính `id` kế tiếp |
| `delete_line` | GHI | `line` |

### mo/repository.py

| Hàm | Loại | Chạm |
|---|---|---|
| `get_mo` | ĐỌC | `manufacturing_order` — không có thì **ném lỗi** |
| `get_mo_or_none` | ĐỌC | `manufacturing_order` — không có thì trả `None` |
| `list_mos` | ĐỌC | `manufacturing_order` |
| `save_mo` | GHI | `manufacturing_order` |

### packing/repository.py

| Hàm | Loại | Chạm |
|---|---|---|
| `get_packing` | ĐỌC | `packing` |
| `packing_of_rounds` | ĐỌC | `packing` — **theo lô** |
| `packing_hourly_of` | ĐỌC | `packing_hourly` |
| `packing_hourly_of_rounds` | ĐỌC | `packing_hourly` — **theo lô** |
| `packed_boxes_pcs` | ĐỌC | `packing_hourly` — Σ(thùng × quy cách) quy ra pcs |
| `save_packing` | GHI | `packing` |
| `add_packing_hourly` | GHI | `packing_hourly` |

### production/repository.py

| Hàm | Loại | Chạm |
|---|---|---|
| `get_production` | ĐỌC | `production` |
| `production_of_rounds` | ĐỌC | `production` — **theo lô** |
| `open_segment_of` | ĐỌC | `line_segment` — **có khoá dòng** |
| `segments_of` | ĐỌC | `line_segment` |
| `open_segments_of` | ĐỌC | `line_segment` |
| `held_line_codes` | ĐỌC | `line_segment`, `line` |
| `hourly_of` | ĐỌC | `hourly_output` |
| `hourly_of_rounds` | ĐỌC | `hourly_output` — **theo lô** |
| `save_segment` | GHI | `line_segment` |
| `save_production` | GHI | `production` |
| `add_hourly` | GHI | `hourly_output` |

### qc/repository.py

| Hàm | Loại | Chạm |
|---|---|---|
| `get_qc` | ĐỌC | `qc_result` |
| `save_qc` | GHI | `qc_result` |

### reports/repository.py

| Hàm | Loại | Chạm |
|---|---|---|
| `mo_progress_rows` | ĐỌC | `v_mo_progress`, `manufacturing_order` |
| `hourly_rows` | ĐỌC | `hourly_output`, `mo_round`, `manufacturing_order` — **một câu duy nhất** |
| `_bin_expr` · `_inside_expr` | — | dựng biểu thức SQL từ sáu mốc giờ, không chạm CSDL |

### round/repository.py

| Hàm | Loại | Chạm |
|---|---|---|
| `progress_row` | ĐỌC | `v_mo_progress` |
| `lock_open_round` | ĐỌC | `mo_round` — **có khoá dòng**, mọi service sửa vòng đều bắt đầu từ đây |
| `rounds_of` | ĐỌC | `mo_round` |
| `get_step` | ĐỌC | `mo_step` |
| `steps_of` | ĐỌC | `mo_step` |
| `steps_of_rounds` | ĐỌC | `mo_step` — **theo lô** |
| `names_of_users` | ĐỌC | `app_user` — một câu cho cả danh sách id |
| `open_round` | GHI | `mo_round` |
| `open_step` | GHI | `mo_step` |
| `close_step` | GHI | `mo_step` — ghi bằng cách sửa thuộc tính ORM, xem §4.3 |

### scan/repository.py

| Hàm | Loại | Chạm |
|---|---|---|
| `scan_seen_recently` | ĐỌC | `scan_dedupe` |
| `scan_remember` | ĐỌC+GHI | `scan_dedupe` |

### warehouse_in · warehouse_out

| Hàm | Loại | Chạm |
|---|---|---|
| `get_warehouse_in` | ĐỌC | `warehouse_in` |
| `save_warehouse_in` | GHI | `warehouse_in` |
| `get_warehouse_out` | ĐỌC | `warehouse_out` |
| `save_handover` | GHI | `warehouse_out` |

### common/event_log/repository.py

| Hàm | Loại | Chạm |
|---|---|---|
| `events_of` | ĐỌC | `mo_event` — một TRANG, mới nhất trước |
| `count_events` | ĐỌC | `mo_event` |
| `log` | GHI | `mo_event` — **không có hàm sửa/xoá** |

`mo_event` là sổ chỉ ghi thêm ở tầng CSDL: hai RULE `mo_event_no_update` và
`mo_event_no_delete` biến mọi lệnh sửa/xoá thành `DO INSTEAD NOTHING`. Chúng **không
báo lỗi** — câu lệnh đi qua êm và báo "0 dòng".

---

## 3 · View và bảng

### Tám view — nơi mọi số dẫn xuất được tính

| View | Ai đọc |
|---|---|
| `v_round_board` | `board.running_rows` |
| `v_mo_progress` | `board.mo_progress`, `round.progress_row`, `reports.mo_progress_rows` |
| `v_line_time` | `board.line_rows_of_rounds` |
| `v_step_total` | `board.step_totals` |
| `v_round_kpi` | qua `v_round_board` |
| `v_step_time` | qua `v_step_total` |
| `v_hourly_reconcile` | **chưa endpoint nào đọc** |
| `v_packing_reconcile` | **chưa endpoint nào đọc** |

Nguyên tắc ② của BE-PLAN: số dẫn xuất đọc thẳng từ view, không tính lại ở Python — để
con số trên màn hình và con số trong báo cáo không bao giờ lệch nhau.

### Mười tám bảng

`app_user` · `refresh_token` · `manufacturing_order` · `mo_round` · `mo_step` ·
`mo_event` · `line` · `line_segment` · `production` · `hourly_output` · `packing` ·
`packing_hourly` · `qc_result` · `warehouse_in` · `warehouse_out` · `reason_code` ·
`scan_dedupe` · `alembic_version`

---

## 4 · Những chỗ đáng biết

### 4.1 Đọc theo LÔ — chỗ N+1 đã bị chặn

Sáu hàm `*_of_rounds` (`steps_of_rounds`, `line_rows_of_rounds`, `hourly_of_rounds`,
`packing_of_rounds`, `packing_hourly_of_rounds`, `production_of_rounds`) nhận **danh
sách `round_id`** và hỏi một câu cho cả lô.

Trước đây `trace` hỏi từng vòng một nên một MO bốn vòng tốn 25 câu SQL; nay còn 10 câu
bất kể bao nhiêu vòng. `reports.hourly_rows` cũng cùng nguyên tắc: một câu duy nhất,
không phụ thuộc số lệnh đang chạy, và có test đếm số câu lệnh để canh.

### 4.2 Chỗ duy nhất đọc CSDL ngoài `repository.py`

`common/clock.py` — hai câu `SELECT now()` và `SELECT clock_timestamp()`.

Mốc `_at` phải do CSDL sinh, không lấy đồng hồ máy ứng dụng: đồng hồ các máy lệch nhau
thì `submitted_at` không so được với `mo_step.opened_at`, mà cả hệ này sống bằng cách
trừ hai mốc thời gian. `tests/test_kien_truc.py` có test canh đúng chỗ này.

### 4.3 Service vẫn GHI được, qua thuộc tính ORM

`tests/test_kien_truc.py` cấm service dùng `text()`, `select()`, `db.execute`, `db.add`,
`db.get`, `db.scalar` — nhưng **không cấm sửa thuộc tính của đối tượng ORM**, và
SQLAlchemy tự sinh câu `UPDATE` cho những thay đổi đó lúc flush.

Bảy chỗ đang ghi theo đường này: `auth/service.py` (thu hồi refresh), `mo/service.py`
(submit, cancel), `packing/service.py` (kết thúc đóng thùng), `production/service.py`
(đóng đoạn chuyền), `round/service.py` (đóng vòng), `round/repository.py:close_step`.

Không phải lỗi — đó là cách dùng ORM bình thường, và ranh giới giao dịch vẫn do
`uow.transaction()` giữ. Nhưng câu hỏi *"bảng này bị đụng ở đâu"* thì **không trả lời
được bằng cách chỉ đọc `repository.py`**, phải tìm cả những dòng gán thuộc tính.

### 4.4 Hai view chưa ai dùng

`v_hourly_reconcile` (đối soát sản lượng giờ với SX đạt, §7.2b) và
`v_packing_reconcile`. Cả hai đã có sẵn trong `0001_init` nhưng chưa endpoint nào đọc —
sẵn cho màn **Thợ ở trạm** của báo cáo sản xuất, xem `KE-HOACH-BAO-CAO-SAN-XUAT.md`.

---

## 5 · Frontend gọi GET ở đâu

| Service | Đường dẫn |
|---|---|
| `board.service.ts` | `/board/running` · `/board/queue/{station}` · `/board/at/{station}` · `/board/counts` |
| `mo.service.ts` | `/mos` · `/mos/{code}` · `/lines` |
| `production.service.ts` | `/mos/{code}/trace` · `/mos/{code}/events` · `/lines` |
| `catalog.service.ts` | `/reasons` |
| `reports.service.ts` | `/reports/mo-progress` · `/reports/hourly` |

`/lines` gọi từ **hai** service khác nhau — trùng lặp nhỏ, chưa gây sai vì cùng một
đường dẫn và cùng kiểu trả về.

---

## 6 · Phân trang cho mọi API trả DANH SÁCH

> **P0 · P1 · P2 ĐÃ LÀM XONG.** `269 passed, 1 skipped` · `ruff` · `tsc` · `eslint` sạch.
> `/board/running` từ **40,1 KB xuống 9,8 KB**. Chỉ còn **P3** (tách `hourly`/`boxes`
> khỏi `/trace`) là chưa làm. Mọi thay đổi giữ đúng kế hoạch dưới đây.
>
> Một điều phát hiện khi kiểm chứng: test *"hai trang ghép lại không lặp"* **không
> bắt được** việc thiếu khoá phụ — bảng 30 dòng thì Postgres quét tuần tự và vô tình
> trả đúng thứ tự chèn. Thử bỏ khoá phụ ra: test vẫn xanh. Cái canh thật là
> `test_moi_cau_phan_trang_deu_co_khoa_phu` — nó đọc nguyên văn câu SQL đã chạy và
> bắt `ORDER BY` phải có `code`. Bỏ khoá phụ là test này đỏ ngay.

### 6.1 Đường nào trả danh sách, và đang lớn tới đâu

Số đo trên CSDL phát triển hiện tại (88 lệnh mẫu):

| Đường dẫn | Hôm nay | Trần | Cần phân trang |
|---|---|---|---|
| `GET /board/running` | **76 dòng · 40,1 KB** | không có | **CÓ** |
| `GET /board/at/{station}` | tới 28 dòng · 11,4 KB (trạm 4) | không có | **CÓ** |
| `GET /board/queue/{station}` | tới 16 dòng · 2,2 KB | không có | **CÓ** |
| `GET /mos` | 92 dòng | `limit=200` **giấu trong repository** | **CÓ** |
| `GET /reports/mo-progress` | theo `limit` | có `limit`, **thiếu `offset` và `total`** | **CÓ** |
| `GET /mos/{code}/trace` | 10,1 KB, lồng bốn danh sách | không có | **CÓ — cách khác, xem §6.5** |
| `GET /mos/{code}/events` | — | `limit` + `offset` + `total` | **đã có** — dùng chung `PAGE_SIZE` |
| `GET /board/counts` | 6 khoá | cố định | không |
| `GET /lines` | 14 dòng | cố định | không |
| `GET /reasons` | danh mục | cố định | không |
| `GET /reports/hourly` | — | `max_days` 31 + `max_codes` 200 | không |

**`GET /mos` đang cắt LẶNG LẼ.** `mo_repo.list_mos` có `limit: int = 200` viết cứng
trong repository, router không truyền gì và không trả tổng số. Xưởng chạy tới lệnh thứ
201 là màn Kế hoạch **mất lệnh mà không báo gì** — người dùng tưởng lệnh chưa được tạo
rồi tạo lại. Đúng cái bẫy đã gặp một lần ở `events_of`: một giá trị mặc định im lặng
cắt mất dữ liệu của người gọi.

**`GET /board/running` nặng nhất.** 40 KB, và bảng đang chạy tự làm mới **mỗi 10 giây**
trên mọi máy tính bảng. 20 máy là 80 KB/giây chỉ cho một màn hình, chưa ai đi quét gì.

### 6.2 Một khuôn duy nhất — khuôn đã có sẵn

`GET /mos/{code}/events` đang trả `{ items, total }`, FE khai là `EventPage`. **Dùng
lại đúng khuôn đó**, đừng đẻ khuôn thứ hai: hai khuôn thì FE phải nhớ endpoint nào trả
kiểu nào, và chỗ nhớ nhầm không có gì bắt được.

```
GET /board/running?limit=10&offset=0

{ "items": [ … ], "total": 76 }
```

Khai một lần trong `app/common/schemas.py`:

```python
class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
```

Và một dependency dùng chung trong `app/common/deps.py`, kẹp hai đầu ngay tại cửa —
không tin `limit=999999` từ client:

```python
PAGE_SIZE = 10          # một trang 10 dòng — khai MỘT chỗ, mọi endpoint đọc từ đây
PAGE_MAX  = 100         # trần cứng, chặn `limit=999999`

def page_params(limit: int = PAGE_SIZE, offset: int = 0) -> tuple[int, int]:
    return max(1, min(limit, PAGE_MAX)), max(0, offset)

PageDep = Annotated[tuple[int, int], Depends(page_params)]
```

**Một trang là 10 dòng ở MỌI endpoint.** Hai con số trên khai đúng một chỗ; endpoint nào
cũng đọc từ đó chứ không tự đặt số riêng. Mỗi nơi một cỡ trang thì người dùng không
đoán được "xem thêm" sẽ ra bao nhiêu dòng, và test phải nhớ từng con số một.

`limit` vẫn cho gửi lên để màn nào cần thì xin nhiều hơn, nhưng **trần cứng 100**
chặn tại cửa — không tin số client gửi.

### 6.3 Hai cái bẫy phải xử cùng lúc

**Bẫy 1 — thứ tự KHÔNG ổn định thì phân trang trả sai.** `ORDER BY s.accepted_at` mà
hai dòng cùng mốc thì Postgres trả thứ tự tuỳ lần chạy: trang 1 và trang 2 có thể cùng
chứa một dòng, và một dòng khác **biến mất khỏi cả hai**. Mọi câu phân trang phải có
khoá phụ duy nhất:

```sql
ORDER BY s.accepted_at, m.code        -- không phải chỉ accepted_at
```

`events_of` đã học bài này rồi — nó sắp theo `(occurred_at DESC, id DESC)`.

**Bẫy 2 — `total` là một câu SQL thứ hai.** Mỗi request thành hai lượt đi về. Vẫn là
O(1) chứ không phải N+1, nhưng phải **đếm từ đúng câu đã lọc**, không viết câu đếm
riêng. `QUEUE_SQL` là nguồn duy nhất của hàng chờ (§2); câu đếm phải bọc lại chính nó:

```sql
SELECT count(*) FROM ( <QUEUE_SQL của trạm đó> ) q
```

Viết câu đếm riêng thì sớm muộn hai câu trôi khỏi nhau — badge hiện một số, bấm vào ra
số khác, không ai báo lỗi.

**Và khoá `read_cache` phải kèm `limit`/`offset`.** Quên thì trang 2 nhận lại nội dung
trang 1 đang nằm trong cache.

### 6.4 Màn hình nào dùng kiểu nào

Không phải chỗ nào cũng là nút `Trang sau`.

| Màn | Kiểu | Ghi chú |
|---|---|---|
| Bảng đang chạy | **`Trang trước` / `Trang sau`** | vẫn tự làm mới mỗi 10 giây — xem bẫy dưới |
| Sổ lệnh (`/mos`) | **`Trang trước` / `Trang sau`** | màn kế hoạch, không tự làm mới |
| Tiến độ theo lệnh (báo cáo) | **`Trang trước` / `Trang sau`** | sắp **tỉ lệ giảm dần** ở SQL |
| `Cần chú ý` (tổng quan) | **`Trang trước` / `Trang sau`**, 10 việc một trang | danh sách dựng ở FE — xem dưới |
| Hàng đợi, đang ở trạm | **trang đầu + dòng "còn n lệnh nữa"** | người đứng trạm xử từ trên xuống; xử bớt là danh sách tự đẩy lên |
| Nhật ký MO | **`Xem thêm` + `Thu gọn`** | đã làm xong, chỉ đổi sang dùng chung `PAGE_SIZE` |

**Bảng đang chạy vừa chuyển trang vừa tự làm mới — hai thứ này sống chung được**, vì
`offset` nằm TRONG khoá query: làm mới chỉ nạp lại đúng trang đang xem, không kéo ai
về trang 1.

Cái phải lo là **trang cuối rỗng đi trong lúc đang xem**: lệnh đóng bớt thì `total` tụt
xuống dưới `offset`, và người vận hành nhìn một bảng trống trơn rồi tưởng mất hết
lệnh. `RunningTable` có một `useEffect` kéo `offset` về khi điều đó xảy ra.

**Tiến độ theo lệnh sắp theo TỈ LỆ giảm dần, sắp ở SQL.** Đơn 15.000 làm được 7.000
(47%) không "sắp xong" bằng đơn 2.500 làm được 2.000 (80%), nên sắp theo `qty_done`
tuyệt đối là sai câu hỏi. Sắp ở FE còn sai hơn: FE chỉ cầm một trang nên mỗi trang
sẽ sắp riêng một kiểu.

**Thẻ `Cần chú ý` phân trang ở FE**, vì danh sách đó không phải một endpoint — nó
dựng tại chỗ từ bảng đang chạy và hàng đợi Kho xuất. Để cảnh báo không bị thiếu, màn
tổng quan xin hẳn **trang 100 dòng** cho hai nguồn đó thay vì 20 mặc định: cảnh báo
thiếu mà không ai biết là loại thiếu nguy hiểm nhất, vì màn hình trông như đã yên.
Quá 100 vòng đang chạy thì vẫn thiếu — lúc đó cần một endpoint cảnh báo riêng.

**Hai màn trạm thì không chuyển trang.** Người đứng trạm xử việc từ trên xuống chứ
không đi tìm; xử bớt thì danh sách tự đẩy lên. Dòng *"còn n lệnh nữa"* đủ để họ biết
khối lượng còn lại.

### 6.5 Riêng `/mos/{code}/trace`

Trace lồng bốn danh sách trong mỗi vòng. Đo trên MO nặng nhất hiện có:

```
M200082   10,1 KB   2 vòng
  vòng 1: steps=6  lines=1  hourly=12  boxes=0
  vòng 2: steps=3  lines=1  hourly=7   boxes=0
```

Ba trong bốn có **trần tự nhiên**: `steps` tối đa 6 (sáu trạm), `lines` tối đa 14 (mười
bốn chuyền), số vòng thực tế hiếm khi quá 5. Chỉ `hourly` và `boxes` là **không có
trần** — một vòng chạy ba ngày là ~24 dòng sản lượng giờ, chạy một tuần là ~56.

Nên **không phân trang cả cây trace**. Tách hai danh sách vô hạn ra endpoint riêng:

```
GET /mos/{code}/rounds/{round_no}/hourly?limit=&offset=   → Page[HourlyRow]
GET /mos/{code}/rounds/{round_no}/boxes?limit=&offset=    → Page[BoxRow]
```

Trace giữ lại **số đếm** (`hourly_total`, `boxes_total`) để màn hình biết có gì mà mở.
Cùng cách đã làm với nhật ký: trả trang đầu kèm tổng, nút `Xem thêm` gọi endpoint riêng.

### 6.6 Các file phải thay đổi

#### Backend

| File | Thay gì |
|---|---|
| `app/common/schemas.py` | thêm `Page[T]` — `{items, total}`, khai MỘT lần |
| `app/common/deps.py` | thêm `PAGE_SIZE = 10`, `PAGE_MAX = 100`, `page_params` + `PageDep`; kẹp `limit` 1–100 và `offset` ≥ 0 |
| `app/modules/board/repository.py` | `running_rows`, `queue_rows`, `at_station_rows` nhận `limit`/`offset`; thêm `count_running`, `count_queue`, `count_at_station` **bọc lại chính câu SQL đang dùng**; thêm khoá phụ vào mọi `ORDER BY` |
| `app/modules/board/service.py` | ba hàm trả `{items, total}` |
| `app/modules/board/router.py` | ba endpoint nhận `PageDep`; **khoá `read_cache` phải kèm `limit`/`offset`** |
| `app/modules/board/schemas.py` | `response_model=Page[…]` |
| `app/modules/mo/repository.py` | `list_mos` bỏ `limit=200` viết cứng, nhận `limit`/`offset`; thêm `count_mos(status)` |
| `app/modules/mo/router.py` | `GET /mos` nhận `PageDep`, trả `Page[MoOut]` |
| `app/modules/reports/{repository,service,router,schemas}.py` | `mo-progress` thêm `offset` và `total` |
| `app/modules/board/service.py` | `trace` bỏ `hourly`/`boxes` khỏi cây, thay bằng `hourly_total`/`boxes_total` |
| `app/modules/board/router.py` | thêm hai endpoint `…/rounds/{round_no}/hourly` và `…/boxes` |
| `app/modules/board/service.py` (`EVENT_PAGE`) | đọc `PAGE_SIZE`, bỏ hằng số riêng |
| `tests/test_phan_trang.py` | **mới** — xem §6.7 |
| `tests/test_permissions.py` | khai hai endpoint mới vào bảng quyền hoặc `CO_Y_MO` |

#### Frontend

| File | Thay gì |
|---|---|
| `src/types/api.ts` | `export type Page<T> = { items: T[]; total: number }` — dùng lại cho cả `EventPage` |
| `src/types/{board,mo,reports}.ts` | kiểu trả về đổi từ `X[]` sang `Page<X>` |
| `src/services/{board,mo,reports}.service.ts` | truyền `limit`/`offset` |
| `src/constants/queryKeys.ts` | khoá query kèm `limit`/`offset` — thiếu thì `invalidateQueries` trượt |
| `src/hooks/board/useBoard.ts` | trả `{items, total}`; ba màn bảng dùng trang đầu + tổng |
| `src/hooks/reports/useReports.ts` | `useInfiniteQuery` cho `mo-progress` |
| `src/constants/pagination.ts` | **mới** — `PAGE_SIZE` của FE, khai một chỗ; mọi service và hook đọc từ đây |
| `src/components/board/RunningTable.tsx` · `scan/QueueList.tsx` · `station/AtStationTable.tsx` | đọc `data.items`, thêm dòng `còn n lệnh nữa` |
| `src/components/mo/MoTable.tsx` | thêm `Trang trước` / `Trang sau` |
| `src/components/reports/MoProgress.tsx` | thêm `Xem thêm` |
| `src/components/mo/RoundDetail.tsx` | `hourly`/`boxes` gọi endpoint riêng |

### 6.7 Test phải có

1. **Trang 2 không trùng và không sót trang 1** — dựng 30 dòng cùng một mốc thời gian,
   lấy hai trang, hợp lại phải đủ 30 và không lặp. Đây là test bắt bẫy khoá phụ.
2. **`total` khớp số dòng thật**, kể cả khi có lọc `status`.
3. **`limit` bị kẹp** — không gửi gì thì ra đúng 10 dòng; gửi `limit=999999` ra nhiều
   nhất 100.
4. **`offset` âm không làm nổ** — kẹp về 0.
5. **Cache không lẫn trang** — gọi trang 1 rồi trang 2, nội dung phải khác nhau.

### 6.8 Thứ tự nên làm

| | Việc | Vì sao thứ tự này | Công |
|---|---|---|---|
| **P0** | `Page[T]` + `PageDep` + `GET /mos` | `/mos` là chỗ **đang mất dữ liệu lặng lẽ**, và làm nó trước thì có luôn khuôn cho mấy cái sau | ~3h |
| **P1** | Ba đường `/board/*` | nặng nhất, và gọi lại mỗi 10 giây | ~4h |
| **P2** | `/reports/mo-progress` | đã có `limit`, chỉ thêm `offset` + `total` | ~1h |
| **P3** | Tách `hourly`/`boxes` khỏi `/trace` | đụng nhiều nhất ở FE, và chưa ai kêu chậm | ~4h |
