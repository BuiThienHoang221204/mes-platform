# MES Platform — Kế hoạch xây dựng Backend (Python + PostgreSQL)

> Bản v1.1 — 2026-09-14 · **đã đối chiếu với mã nguồn đang chạy**
> Căn cứ: `BRD-v2-chot.md` v2.20 · `DB-GON.md` v2.4 · `demo/mes-v2-console.html` v47
> Đích chạy thật: 1 xưởng · 14 chuyền · ~100–300 lệnh/ngày · 6 trạm quét
>
> Hiện trạng: **30 endpoint · 16 bảng · 59 test xanh trên Postgres thật** ·
> `ruff` sạch · 4 migration (`0001` lược đồ · `0002` dữ liệu hệ thống · `0003` refresh token ·
> `0004` 13 vai RBAC). **Viết tay — `--autogenerate` bị chặn, xem §9.**
>
> **v1.0 → v1.1:** cắt dọc theo tính năng (§2, §3) · đổi `dispatch` → `warehouse` ·
> **phân quyền #26 đã chốt** (§6, BRD §9b) ·
> thêm refresh token có xoay vòng (§6) · token đi bằng cookie httpOnly (§6) ·
> cấu hình gom nhóm kiểu NestJS (§10) · `uv` + `run.sh` thay `pip` + `make` (§10).

---

## 0. Ba nguyên tắc chi phối toàn bộ thiết kế

Ba điều này quyết định mọi lựa chọn kỹ thuật bên dưới. Đọc trước khi đọc phần còn lại.

**① Cơ sở dữ liệu là nơi giữ luật, không phải Python.**
`đạt + hỏng + thiếu = mục tiêu vòng`, `chưa bàn giao thì Setup không nhận được`, `một chuyền không chạy
hai MO cùng lúc`, `nhật ký không sửa không xoá` — tất cả đã là `CHECK`, `EXCLUDE`, `RULE`, chỉ mục duy
nhất trong `DB-GON.md`. Backend **không kiểm lại** những luật đó rồi mới ghi; nó ghi, và **dịch lỗi của
DB thành thông báo tiếng Việt** cho người vận hành.

> Vì sao: kiểm ở Python thì chỉ chặn được đường đi qua Python. Import CSV, script vá dữ liệu, một anh DBA
> gõ tay — ba đường đó đều lọt. Và khi hai người bấm cùng lúc thì kiểm-rồi-ghi luôn có khe hở giữa hai
> thao tác; `CHECK` thì không.

**② Số dẫn xuất đọc từ view, không tính trong Python.**
`v_step_total`, `v_line_time`, `v_round_kpi`, `v_mo_progress`, `v_hourly_reconcile`, `v_round_board` đã
có sẵn. Backend `SELECT` rồi trả ra. Tính lại bằng Python là tạo nguồn sự thật thứ hai — và hai nguồn thì
có ngày lệch nhau.

**③ Mọi mốc giờ do server sinh, không nhận từ client.**
BRD §9 chốt *"Timer tính từ timestamp BE, FE chỉ hiển thị"*. Máy tính bảng ngoài chuyền sai giờ là chuyện
thường. Dùng `DEFAULT now()` của Postgres (giờ của transaction) cho mọi `_at`.

---

## 1. Chọn stack — và vì sao

| Thành phần | Chọn | Vì sao chọn cái này |
|---|---|---|
| Web framework | **FastAPI** | Sinh OpenAPI sẵn để FE và máy quét đối chiếu; validate bằng Pydantic v2 ngay ở biên |
| ORM | **SQLAlchemy 2.0 (sync)** | Kiểu `Mapped[...]` rõ ràng; quan trọng hơn: viết transaction và `FOR UPDATE` bằng lối **đồng bộ** dễ đọc và khó sai hơn async |
| Driver | **psycopg 3** | Bản đang được bảo trì; hỗ trợ tốt `timestamptz`, `text[]`, enum |
| Migration | **Alembic** | DDL trong `DB-GON.md` là migration đầu tiên, chép gần như nguyên văn |
| Validate | **Pydantic v2** | Schema vào/ra tách khỏi model DB |
| Test | **pytest + Postgres thật (testcontainers)** | Xem §8 — đây là lựa chọn quan trọng nhất của kế hoạch |
| Chạy | **gunicorn + uvicorn worker** | Nhiều tiến trình, mỗi tiến trình một pool kết nối |
| Đóng thùng | **Docker + compose** | Một lệnh dựng cả API lẫn Postgres, giống nhau ở máy dev và máy xưởng |

### Vì sao **sync** chứ không async

Tải thật của xưởng là **vài trăm lượt ghi mỗi ngày**, đỉnh điểm là lúc Kho phát lệnh đầu ca (100 lệnh
trong vài phút). Đó không phải bài toán I/O-bound cần async.

Đổi lại, phần khó của hệ này là **giao dịch và khoá**: quét đồng thời, `SELECT FOR UPDATE`, `RULE`
chặn ghi đè. Code đồng bộ đọc thẳng từ trên xuống, ai cũng rà được. Async thêm một lớp `await` vào đúng
chỗ dễ sai nhất mà không đổi lại được gì.

FastAPI chạy hàm `def` (không phải `async def`) trong threadpool — vẫn phục vụ song song bình thường.

---

## 2. Chia tầng

Cắt **DỌC theo tính năng**, không cắt ngang theo tầng kỹ thuật. Mở một thư mục trong
`modules/` là thấy đủ mọi tầng của tính năng đó — đúng chỗ `src/modules/` của NestJS,
hay một "app" của Django:

```
app/
├─ modules/            ── 11 lát cắt dọc, mỗi thư mục một tính năng ────────
│  ├─ mo/              models.py · schemas.py · repository.py · service.py · router.py
│  ├─ warehouse/       trạm 0 — bàn giao
│  ├─ qc/              trạm 2
│  ├─ production/      trạm 4 — chuyền · chốt sổ · sản lượng giờ
│  ├─ packing/         đóng thùng (song song với sản xuất)
│  ├─ receipt/         trạm 5 — nhập kho
│  ├─ scan/            quét — một cửa cho cả sáu trạm
│  ├─ auth/            đăng nhập · token thiết bị
│  ├─ catalog/         line · reason_code
│  ├─ board/           màn hình điều hành (chỉ đọc, không có models.py)
│  └─ round/           ★ TRỤC CHUNG — vòng chạy + bước, KHÔNG có router
├─ common/             ── hạ tầng mọi module đều dùng ─────────────────────
├─ db/                 session · migrations
├─ router.py           gộp 10 router — prefix /v1 đặt DUY NHẤT ở đây
└─ main.py
```

**Bộ 5 file của một tính năng** (thiếu file nào cũng được, miễn có lý do):

| File | Việc |
|---|---|
| `models.py` | bảng SQLAlchemy |
| `schemas.py` | DTO vào/ra — hợp đồng với FE |
| `repository.py` | câu truy vấn. **Chỉ file này được viết SQL** |
| `service.py` | luật nghiệp vụ + **ranh giới transaction** (`@transactional`) |
| `router.py` | HTTP. Không luật nghiệp vụ, không chạm CSDL |

**Quy tắc một chiều trong mỗi tính năng:** `router → service → repository → models`.
Không có mũi tên ngược.

### Giao dịch: `@transactional` ở service, không ở router

Tương đương `@Transactional()` của NestJS/Spring với propagation **REQUIRED** — hàm
được gọi từ trong một giao dịch đang chạy thì **nhập vào**, không mở cái mới.

```python
@transactional
def handover(db, *, code, actor_id):
    _, rnd = round_service.lock_round(db, code)   # SELECT … FOR UPDATE
    ...
```

Vì sao không để router mở như trước:

* **Khoá dòng phải nằm chung giao dịch với phần ghi.** `lock_round` khoá vòng đang
  mở và nhả lúc commit. Tách ra thì hai người bấm cùng lúc cùng đi qua.
* **Phạm vi là quyết định nghiệp vụ.** `handover_batch` gọi `handover` 100 lần
  trong MỘT giao dịch (§7A: một mã hỏng thì cả lô không ai được giao). Cùng một
  `handover`, hai ranh giới — chỉ service biết.
* **Router không còn chạm CSDL**, nên không thể lỡ mở một giao dịch chỉ-đọc rồi
  làm service tưởng mình đang lồng.

Ba ngoại lệ có chủ ý:

| Chỗ | Vì sao |
|---|---|
| `catalog/router.py`, `GET /mos/{code}` | chỉ đọc — không cần đơn vị công việc |
| `auth_service.refresh` | **không** `@transactional`: phát hiện dùng lại thì phải thu hồi và **commit** trước, rồi mới `raise` — gộp chung thì câu raise huỷ luôn việc thu hồi |
| `deps.current_actor` | đọc người dùng xong `db.rollback()` để trả session về trạng thái sạch |

`tests/test_uow.py` canh cả ba lời hứa, và `tests/test_deps.py` canh cái cuối.

### `round/` là trục chung, không phải một tính năng

14/15 bảng khoá theo `round_id`, và mọi thao tác trạm đều mở đầu bằng
`round_repo.lock_open_round`. Nên `round/` KHÔNG có `router.py` — nó không phải màn
hình của ai, mà là thứ `qc/`, `receipt/`, `mo/`, `scan/` đều import.

Đây chính là chỗ cắt dọc trả giá, và nó lộ ngay trong khối import — ví dụ
`qc/service.py`:

```python
from app.common import repository as event_repo
from app.mo.models import ManufacturingOrder
from app.qc import repository as qc_repo
from app.round import repository as round_repo
from app.round import service as round_service       # ← QC FAIL mở vòng mới
```

Đọc khối import là biết ngay tính năng này phụ thuộc vào những tính năng nào. Bên
cắt ngang thì chỗ này chỉ là `from app import repositories as repo` — che mất
toàn bộ quan hệ.

### Vì sao `common/` và `db/` nằm NGOÀI `modules/`

`modules/` chỉ chứa **tính năng** — thứ có thể kể tên bằng ngôn ngữ của người ở xưởng.
`common/` và `db/` không kể được như vậy: chúng là hạ tầng mọi module đều dựa vào.

Ranh giới này có ích lúc đọc code: thấy `app.modules.*` là biết đang đụng vào nghiệp
vụ, thấy `app.common.*` là biết đang đụng vào thứ dùng chung — sửa nó thì **mọi**
module chịu ảnh hưởng.

### `common/` — thứ mọi tính năng đều dùng

```
common/
├─ base.py         Base · khoá UUID · 4 kiểu ENUM của Postgres
├─ enums.py        MoStatus · QcVerdict · SegmentKind · ReasonGroup
│                  + STEP_NAMES · RETURN_TO_KHO · RETURN_TO_BANCHO
├─ schemas.py      MoCode · StationNo · ErrorOut · OkOut
├─ deps.py         DbDep · ActorDep · StationDep + 3 security scheme cho /docs
├─ cookies.py      đặt/xoá cookie token — MỘT chỗ biết tên và thuộc tính cookie
├─ models.py       mo_event — nhật ký, 9/12 file service ghi vào
├─ repository.py   log · events_of
├─ config.py · errors.py · security.py · logging.py · clock.py
```

### Từng có `registry.py`, đã bỏ — 2026-09-15

File đó liệt kê 16 model để `Base.metadata` đầy đủ, vai trò `INSTALLED_APPS` của
Django. Bỏ vì **không còn khách hàng nào**: nó chỉ phục vụ `target_metadata` của
Alembic, mà autogenerate và `alembic check` đều đã chặn (xem §9).

Hệ quả cần biết nếu ai định dùng lại lối so-bằng-metadata:

| Lấy `Base` từ đâu | `Base.metadata` có |
|---|---|
| `common/base.py` | **0 bảng** — chỉ định nghĩa `Base`, chưa nạp model nào |
| `import app.main` | **15/16** — thiếu `scan_dedupe`, vì `scan/service.py` dùng bảng đó qua SQL thô chứ không import lớp model |
| `registry.py` *(đã bỏ)* | 16 |

Con số 15 là cái bẫy: file migration sinh ra chỉ có đúng một dòng
`op.drop_table('scan_dedupe')` lẫn giữa 18 dòng khác — review lướt là cho qua.

Vì vậy `env.py` đặt thẳng `target_metadata = None` chứ không trỏ vào `common/base.py`:
rỗng thì autogenerate đòi xoá cả 16 bảng, mà lại trông như đang có cấu hình đúng.

**`Base` thì vẫn giữ nguyên** — nó không phải để đếm bảng. Không kế thừa `Base` thì
lớp không thành ORM model: `select(X)` ném `ArgumentError`, `db.add(X())` ném
*"Class X is not mapped"*. Mọi `models.py` vẫn import từ `common/base.py`.

### Vì sao cắt dọc

Đo trên chính repo này trước khi đổi: sửa MO phải mở **11 file / 5 thư mục**, sửa
QC **7 file / 5 thư mục**. Cắt dọc đưa về **1 thư mục**.

Cách này là mặc định của Django (mỗi "app" một thư mục) và là cấu trúc của Netflix
Dispatch — một FastAPI chạy production. Không phải sáng tạo riêng.

**Cái mất:** quy tắc "1 file = 1 bảng" không giữ được cho ba thư mục nhiều bảng —
`production/models.py` gom `production` + `line_segment` + `hourly_output`,
`round/models.py` gom `mo_round` + `mo_step`, `catalog/models.py` gom `line` +
`reason_code`. Tám thư mục còn lại vẫn một bảng một file. **Thứ tự class trong ba
file gộp giữ đúng thứ tự bảng trong DB-GON.md** để vẫn dò theo tài liệu được.

### Không dựng tầng cho có

* `catalog/` KHÔNG có `service.py` — không có luật nghiệp vụ nào, router gọi thẳng repository.
  (`auth/` từng như vậy, tới khi thêm refresh token thì nó có luật thật: xoay vòng, bắt dùng lại.)
* `board/` KHÔNG có `models.py` — nó chỉ đọc view, không sở hữu bảng nào.
* `warehouse/` KHÔNG có `schemas.py` — bàn giao không nhận body nào.

Dựng file rỗng cho đủ bộ là dựng tầng cho có.

### SQL chỉ được nằm trong `repository.py`

`router.py` và `service.py` KHÔNG được viết `select(...)` hay `db.execute(text(...))`.
Không phải để "sau này đổi CSDL" — sẽ không đổi — mà để khi cần biết "bảng này
bị đụng ở đâu" thì chỉ phải mở một file, đúng file trùng tên bảng.

Hàm repository gọi chéo tính năng nên tên phải tự nói rõ nó ở đâu ra:
`get_user_by_id` chứ không `get_by_id`, `list_reasons` chứ không `list_active`,
`scan_remember` chứ không `remember` — đọc `auth_repo.get_user_by_id(...)` là đủ hiểu.

**Đã trả xong** (2026-09-15): các câu SELECT từ view (`v_step_total`, `v_line_time`,
hàng đợi từng trạm) từng nằm trong `board/service.py` — nay ở `board/repository.py`.
Cùng ngày dọn nốt `v_mo_progress` trong `round/service.py` — chỗ bị sót ở lượt đầu.

**Không còn ngoại lệ nào, và giờ có TEST canh.** `tests/test_kien_truc.py` đọc mã
nguồn, bắt đỏ nếu service viết `text(...)` / `select(...)` / `db.add(...)` /
`db.execute(...)`, hoặc router chạm CSDL. Đã kiểm ngược: đưa một `db.add()` trở lại
service thì test đỏ ngay.

Ba thứ service VẪN được giữ, có chủ ý:

| Giữ ở service | Vì sao |
|---|---|
| `db.flush()` | không ghi thêm gì, chỉ đẩy thay đổi đang treo xuống sớm để ràng buộc nổ đúng dòng |
| `mo.status = ...` — gán thuộc tính đối tượng ORM | đây là đổi **trạng thái nghiệp vụ**. Bọc vào `mo_repo.set_status()` thì đẻ ra một rừng hàm một dòng, đọc `submit()` phải nhảy file bốn lần |
| `@transactional` | ranh giới giao dịch — xem mục riêng bên dưới |

Ghi xuống CSDL thì gọi `repo.save_*()`: `save_mo` · `save_handover` · `save_qc` ·
`save_segment` · `save_production` · `save_packing` · `save_receipt` · `save_refresh`.

Lấy giờ ghi vào cột `_at` thì gọi `clock.db_now(db)` hoặc `clock.db_clock(db)` —
`common/clock.py` là chỗ duy nhất được viết hai câu SQL đó, và có test canh.

Gom xong lộ thêm hai thứ mà lúc SQL còn rải rác thì không ai thấy:

* Câu **liệt kê** hàng đợi và câu **đếm badge** trước nằm rời nhau, không gì buộc
  chúng khớp. Nay cả hai dựng từ một `QUEUE_SQL` duy nhất — badge và danh sách
  không thể lệch nhau được nữa, và `station_counts` từ **7 câu SQL còn 1**.
* `trace` hỏi CSDL **từng vòng một** — MO bốn vòng tốn 25 câu. Đọc theo lô
  (`steps_of_rounds`, `hourly_of_rounds`, …) đưa về **10 câu, cố định**.
  `tests/test_board.py` canh không cho nó quay lại.

#### Trong repository: khi nào ORM, khi nào SQL thô

Đo ngày 2026-09-15: **32 hàm ORM · 9 hàm SQL thô**, và 9 cái đó không rải ngẫu nhiên.

> **Mặc định là ORM.** Chỉ chuyển sang `text(...)` khi rơi vào một trong ba:
> 1. đọc **view**
> 2. **JOIN / gộp / `UNION`** nhiều bảng
> 3. dùng thứ **riêng của Postgres** mà ORM diễn đạt dài hơn — `ON CONFLICT`,
>    `make_interval`, hàm thời gian

Ba điều kiện đó phủ đúng 9 hàm hiện có, không thừa không thiếu — toàn bộ nằm ở
`board/` (view, hàng đợi) và `scan/` (upsert chống bắn trùng), cộng `round.close_step`
lấy `SELECT now()` từ CSDL.

Vì sao không gộp về một kiểu:

* **Hết về ORM** — phải khai 7 lớp model chỉ để đọc 7 view, mà `EXCLUDE USING gist`
  và chỉ mục một phần thì SQLAlchemy không diễn đạt nổi. Câu hàng đợi 4 dòng SQL sẽ
  thành hơn chục dòng `select().join().outerjoin()`.
* **Hết về SQL thô** — vứt 32 hàm đang rất gọn, và mất `.with_for_update()`: bốn chỗ
  khoá dòng hiện là một lời gọi phương thức, thành chuỗi ký tự thì quên là không ai báo.

#### Lọc theo danh sách: `IN` hay `ANY`

> **ORM → `.in_(ids)`   ·   SQL thô → `= ANY(:ids)`**

Không phải chuyện thẩm mỹ. Đo thật trong SQL thô:

| | Viết thế nào | Danh sách rỗng |
|---|---|---|
| `= ANY(:ids)` | truyền thẳng `{"ids": ids}` | **OK, 0 dòng** |
| `IN :ids` | phải thêm `.bindparams(sa.bindparam("ids", expanding=True))` | **ProgrammingError** |

Quên `expanding=True` thì báo `syntax error at or near "$1"` — không hề nhắc tới
nguyên nhân thật. Còn danh sách rỗng là chuyện xảy ra thật: MO vừa tạo thì chưa có
vòng nào, `line_rows_of_rounds` nhận `[]`.

Bên ORM ngược lại: `.in_([])` được SQLAlchemy dịch thành `1 != 1`, an toàn sẵn.

Hiện toàn dự án có **đúng một** chỗ dùng `ANY` — `board.line_rows_of_rounds`, vì nó
đọc view `v_line_time` nên buộc phải là SQL thô.

> Giới hạn cần biết: `IN` sinh **mỗi phần tử một tham số**, mà Postgres chỉ nhận tối đa
> **65.535** tham số một câu. Đo thật: 60.000 id chạy được (558 ms), **70.000 id gãy**;
> `ANY` gói cả danh sách thành một tham số nên 200.000 id vẫn chạy (883 ms). Ở đây
> danh sách là số vòng của một MO — nhiều nhất chục cái, cách ngưỡng đó vài nghìn lần.
> Nếu có ngày bạn định nhét vài chục nghìn id vào `IN`, thường cách đúng không phải đổi
> sang `ANY` mà là viết `JOIN` để dữ liệu khỏi đi vòng qua Python.

### Tên lộ ra ngoài thì tiếng Anh, tên trong nhà thì tiếng Việt

Ranh giới rõ ràng:

| Tiếng Anh | Vì sao |
|---|---|
| `tags` trên /docs, đường dẫn URL, tên bảng, tên cột, tên class, tên file | lộ ra ngoài — FE sinh client tự động từ OpenAPI, tag thành tiền tố tên hàm; DBA đọc bảng; người ngoài đọc repo |
| Docstring, comment, `message` trả cho người vận hành | chỉ người trong nhà đọc, và câu tiếng Việt hiện thẳng lên màn hình xưởng |

Mười một tag: `auth` · `mo` · `scan` · `warehouse` · `qc` · `production` ·
`packing` · `receipt` · `board` · `catalog` (`hourly.py` dùng chung tag
`production` vì cùng một màn hình chuyền).

### Thứ tự router là hành vi, không phải thẩm mỹ

Starlette dò route **theo thứ tự đăng ký**. `app/router.py` giữ
nguyên thứ tự của bản gộp cũ; đảo thứ tự `include_router` là đổi định tuyến.

Sau mỗi lần sửa cấu trúc router, kiểm bằng cách dựng app rồi so **cả tập lẫn thứ
tự** endpoint với bản trước, và bắn thử request thật: route đúng thì ra
401/403/500, route hỏng thì ra **404 mà không báo lỗi gì**.

### Vai trò dùng HẰNG, không dùng chuỗi thô

`ROLE_KHO` · `ROLE_SETUP` · `ROLE_QC` · `ROLE_BANCHO` · `ROLE_LEADER` ·
`ROLE_PACKING` · `ROLE_PLANNER` khai ở `app/common/security/actor.py`, và `STATION_ROLE`
dựng từ chính các hằng đó. Viết `require_role("LEADER")` rải khắp 11 file router
thì một lỗi gõ thành một endpoint không ai vào được — fail-closed nên không nổ,
chỉ âm thầm chặn đúng người cần dùng.

### Quy ước đặt tên DTO

**Request mang tên HÀNH ĐỘNG, không mang tên bảng.** `MoCreateIn` nói rõ payload
dùng để tạo; `MoIn` thì nhìn vào không biết tạo hay sửa. Hậu tố `In` / `Out` giữ
nguyên thay vì `Dto` kiểu Nest: cả thư mục `schemas/` đã là DTO rồi, và Python
không có thói quen gắn vai trò vào tên type (không ai viết `MoInterface`).

    MoCreateIn · MoImportIn · MoCancelIn
    QcDecideIn · LineAssignIn · LineStartIn · LineHoldIn
    ProductionCloseIn · PackingFinishIn

**Hai hành động khác nhau thì hai DTO khác nhau, kể cả khi cùng field.**
`/lines/{code}/assign` và `/lines/{code}/start` đều chỉ nhận `line_code` nhưng
vẫn tách `LineAssignIn` / `LineStartIn`, và `LineHoldIn` KHÔNG kế thừa hai cái
kia — `LineHoldIn(LineAssignIn)` đọc thành "dừng là một loại gán". Thêm field
cho một hành động sau này cũng không đụng hai hành động còn lại.

### Một tính năng không nhất thiết đủ 5 file

`schemas.py` nhóm theo **hợp đồng với FE**, nên số DTO không tỉ lệ với số bảng hay
số hàm service:

| Trường hợp | Ví dụ |
|---|---|
| **Nhiều thao tác dùng chung một payload** | `warehouse` · `qc` · `round` đều kích hoạt bằng cùng `ScanIn` → nằm ở `scan/schemas.py` |
| **Có service không lộ ra HTTP** | `round/service.py` chỉ được service khác gọi — `round/` không có `router.py` |
| **Một tính năng gánh nhiều màn hình** | `production/schemas.py` có payload của **năm** endpoint: gán chuyền · chạy · dừng · chốt sổ · sản lượng giờ |

### Đừng dựng tầng cho có

Repository ở đây là **nơi chứa câu truy vấn**, không phải một lớp trừu tượng để "sau này đổi sang MongoDB".
Sẽ không đổi. Mọi luật quan trọng đang nằm trong `CHECK` và `EXCLUDE` của Postgres — đổi CSDL là viết
lại luật, không phải thay một class.

Cụ thể: **không** viết interface + implementation cho mỗi repo, **không** bọc SQLAlchemy trong một lớp
"Unit of Work" tự chế (`Session` đã là Unit of Work), **không** tạo entity riêng rồi map qua lại
với model — 16 bảng không đủ phức tạp để trả giá cho tầng ánh xạ đó.

---

## 3. Cây thư mục

```
mes-backend/
├─ app/
│  ├─ main.py              tạo FastAPI, middleware, healthz, ánh xạ lỗi
│  ├─ router.py            gộp 10 router — prefix /v1 đặt DUY NHẤT ở đây
│  │
│  ├─ common/              ── thứ mọi tính năng đều dùng ──────────────────
│  │  ├─ base.py           Base · khoá UUID · 4 kiểu ENUM
│  │  ├─ enums.py          MoStatus · QcVerdict · SegmentKind · ReasonGroup
│  │  │                    + STEP_NAMES · RETURN_TO_KHO · RETURN_TO_BANCHO
│  │  ├─ schemas.py        MoCode · StationNo · ErrorOut · OkOut
│  │  ├─ deps.py           DbDep · ActorDep · StationDep (+ security scheme)
│  │  ├─ cookies.py        đặt/xoá cookie token — MỘT chỗ biết tên cookie
│  │  ├─ models.py         mo_event — nhật ký, RULE chặn UPDATE/DELETE
│  │  ├─ repository.py     log · events_of
│  │  ├─ config.py         Pydantic Settings, đọc từ biến môi trường
│  │  ├─ errors.py         DomainError + bảng ánh xạ lỗi DB → câu tiếng Việt
│  │  ├─ security.py       xác thực người + thiết bị trạm, 7 hằng ROLE_*
│  │  ├─ logging.py        log JSON, gắn request-id
│  │  └─ clock.py          DUY NHẤT một chỗ lấy giờ (để test tua được)
│  │
│  ├─ modules/             ── 11 lát cắt dọc, mỗi thư mục một tính năng ──
│  │  ├─ round/            ── ★ TRỤC CHUNG, không có router ───────────────
│  │  │  ├─ models.py      mo_round · mo_step
│  │  │  ├─ schemas.py     RoundOut · StepOut
│  │  │  ├─ repository.py  lock_open_round ← chốt chống đua của cả hệ thống
│  │  │  ├─ service.py     mở/đóng vòng — DUY NHẤT một chỗ
│  │  │  └─ step_service.py  mở/đóng bước, chặn nhảy bước
│  │  │
│  │  ├─ mo/               manufacturing_order · Kế hoạch (Planner)
│  │  ├─ warehouse/        warehouse · trạm 0, bàn giao lẻ + theo lô
│  │  ├─ qc/               qc_result · trạm 2, FAIL → mở vòng mới về Kho
│  │  ├─ production/       production · line_segment · hourly_output · trạm 4
│  │  │                    (router gánh cả 5 endpoint, gồm sản lượng giờ)
│  │  ├─ packing/          packing · song song với sản xuất
│  │  ├─ receipt/          receipt · trạm 5, COMPLETED hoặc mở vòng mới
│  │  ├─ scan/             scan_dedupe + mocode.py · một cửa cho 6 trạm
│  │  ├─ auth/             app_user · refresh_token · đăng nhập, xoay vòng token
│  │  ├─ catalog/          line · reason_code (không service)
│  │  └─ board/            màn hình điều hành (không models — chỉ đọc view)
│  │
│  └─ db/
│     ├─ session.py        engine, sessionmaker, dependency get_db
│     └─ migrations/       Alembic — DDL, trigger, view viết tay bằng SQL thô
│
├─ tests/                  59 test, tất cả chạy trên Postgres thật
│  ├─ conftest.py          dựng Postgres bằng testcontainers, chạy migration
│  ├─ test_constraints.py  từng CHECK/EXCLUDE/RULE phải THẬT SỰ chặn
│  ├─ test_flow.py         vòng lặp 9.000 + 1.000 · QC FAIL → về Kho
│  ├─ test_auth.py         xoay vòng refresh · bắt dùng lại · thu hồi
│  ├─ test_cookies.py      httpOnly · Path hẹp · hạn khớp token   (không cần DB)
│  ├─ test_config.py       đơn vị thời gian có khớp tên biến không (không cần DB)
│  └─ test_mocode.py       đọc mã QR thô                          (không cần DB)
├─ run.sh                  thay `make` — Windows không có sẵn
├─ stop-port.ps1           giải phóng cổng; uvicorn --reload đẻ con giữ socket
├─ .env / .env.example     cấu hình; .env KHÔNG lên git
├─ uv.lock                 ghim đúng 50 gói — `pip` không sinh được, `uv` thì có
└─ pyproject.toml
```

Mỗi thư mục tính năng dùng cùng một bộ tên: `models.py` · `schemas.py` ·
`repository.py` · `service.py` · `router.py`. Biết tên tính năng là biết đường
dẫn, không phải dò.

## 4. Bề mặt API

Chia theo **trạm**, đúng như người vận hành nghĩ — không chia theo bảng.

| Nhóm | Endpoint | Ghi chú |
|---|---|---|
| **Đăng nhập** | `POST /v1/auth/login` · `/refresh` · `/logout` | cookie httpOnly, refresh xoay vòng |
| | `POST /v1/auth/station-token` | token gắn vào THIẾT BỊ ở trạm · chỉ Planner |
| **Quét** | `POST /v1/scan` | body chỉ `{raw}` — **trạm lấy từ token thiết bị** |
| **Lệnh** | `POST /v1/mos` · `POST /v1/mos/import` | tạo lẻ · nhập từ CSV |
| | `POST /v1/mos/{code}/submit` · `POST /v1/mos/{code}/cancel` | huỷ bắt buộc có lý do |
| **Kho** | `POST /v1/warehouse/{code}/handover` · `POST /v1/warehouse/handover-batch` | §7A cả lô |
| **QC** | `POST /v1/qc/{code}` | `{result, reason_code_id?, reason_text?}` |
| **Sản xuất** | `POST /v1/lines/{code}/assign` · `/start` · `/hold` | hold bắt buộc lý do |
| | `POST /v1/production/{code}/close` | 3 số + 2 lý do |
| **Đóng thùng** | `POST /v1/packing/{code}/start` · `/finish` | |
| **Nhập kho** | `POST /v1/receipt/{code}/complete` | trả về `COMPLETED` hoặc `ROUND_OPENED` |
| **Sản lượng giờ** | `POST /v1/hourly/{code}` | |
| **Màn hình** | `GET /v1/board/running` · `/queue/{station}` · `/counts` | đọc view |
| **Truy cứu** | `GET /v1/mos/{code}/trace` | mọi vòng · mọi bước · năng suất line · sản lượng giờ |
| **Danh mục** | `GET /v1/lines` · `GET /v1/reasons` | |
| **Vận hành** | `GET /healthz` · `GET /readyz` | `/readyz` kiểm cả kết nối CSDL |

**30 endpoint**, 11 nhóm `tags` trùng tên với 11 thư mục trong `app/modules/`.

### `POST /v1/scan` — cửa vào quan trọng nhất

```
{ raw: "XM068820" }          + header X-Station-Token  →  trạm 2
   ↓ đọc mã     (regex M + 6 số, sửa O→0 và I/L→1, từ chối 7 số và nhiều mã)
   ↓ chống bắn trùng  (cùng mã + cùng trạm trong 2 giây → trả lại kết quả cũ)
   ↓ tìm lệnh + khoá vòng đang mở
   ↓ gọi service của trạm đó
   ↓ trả { ok, mo_code, station, message, state }
```

**Chống bắn trùng phải làm ở server**, không chỉ ở FE. Đầu đọc bắn hai lần là chuyện phần cứng; FE có
thể bị F5 giữa chừng. Cách làm: bảng `scan_dedupe(mo_id, station, at)` với `UNIQUE (mo_id, station)` cập
nhật theo kiểu upsert — trùng trong cửa sổ 2 giây thì trả lại **đúng kết quả lần trước**, không báo lỗi.

> Việc đọc mã (`docMaMO` trong demo) chuyển sang BE **nguyên văn**, kèm đủ 6 tình huống ở BRD §1b.2 làm
> test. Đây là chỗ dễ tưởng là đơn giản nhất mà sai thì hỏng nặng nhất.

---

## 5. Mã lỗi — nói đúng câu người vận hành cần nghe

Postgres trả `IntegrityError` với tên constraint. `core/errors.py` đổi tên đó thành thông báo:

| Tên constraint | HTTP | Thông báo |
|---|---|---|
| `production_balances` (trigger) | 409 | `Đạt 9.000 + hỏng 500 + thiếu 300 = 9.800, phải đúng bằng 10.000 — đang hụt 200` |
| `ng_needs_reason` | 422 | `Có 500 PCS hỏng — bắt buộc ghi LÝ DO HỎNG` |
| `short_needs_reason` | 422 | `Làm thiếu 500 PCS — bắt buộc ghi LÝ DO THIẾU` |
| `production_no_update` (RULE) | 409 | `Vòng 2 đã chốt sổ SX rồi` |
| `packing_within_ok` (trigger) | 409 | `Đóng 9.300 vượt SL đạt của SX (9.000)` |
| `mo_round_one_open` | 409 | `MO đã có một vòng đang chạy` |
| `line_run_no_overlap` | 409 | `Chuyền L02 đang chạy MO khác trong khung giờ này` |
| `handover_needs_print` *(đã bỏ ở v2.18)* | — | — |
| `mo_lock_after_submit` (trigger) | 409 | `MO đã Submit — không sửa được. Huỷ rồi tạo lệnh mới (§4A)` |

Một bảng ánh xạ duy nhất, dùng chung — **không** rải `try/except` ở từng service. Thông báo lấy đúng chữ
đã dùng trong demo để người vận hành không phải học lại.

---

## 6. Xác thực và phân quyền

Ba loại token, ba việc khác nhau:

| Token | Sống | Đi bằng | Thu hồi được? |
|---|---|---|---|
| **access** | 15 phút | cookie `mes_access` (`Path=/`) hoặc header `Authorization: Bearer` | không cần — xem dưới |
| **refresh** | 7 ngày | cookie `mes_refresh` (`Path=/v1/auth`) | **có**, bảng `refresh_token` |
| **station** | 365 ngày | header `X-Station-Token` | không — nạp tay vào máy ở trạm |

Access token **không cần thu hồi riêng**: `common/deps.current_actor` đọc lại bản ghi người dùng ở
**mọi** request, nên tắt `is_active` là chặn ngay lập tức, không phải đợi token hết hạn.

### Refresh token: xoay vòng và bắt dùng lại

Refresh dùng **đúng một lần**. Mỗi lần `POST /v1/auth/refresh` phát ra cặp mới và đánh dấu cái cũ đã
dùng. Gửi lại một refresh đã dùng nghĩa là **có người giữ bản sao** — không biết bản sao ở máy nào, nên
thu hồi CẢ CHUỖI của người đó và bắt đăng nhập lại.

Ba quyết định:

* **Refresh không phải JWT** mà là chuỗi ngẫu nhiên 64 ký tự. Lần refresh nào cũng phải tra CSDL để xoay
  vòng, nên chữ ký JWT không tiết kiệm gì; mà lộ `jwt.secret` thì kẻ tấn công tự ký được JWT, còn chuỗi
  ngẫu nhiên thì không đoán ra.
* **Lưu bằng băm SHA-256**, không lưu chuỗi gốc — rò CSDL cũng không dựng lại được token. Không dùng
  bcrypt ở đây: token đã ngẫu nhiên nên không có gì để dò từ điển, mà refresh chạy mỗi 15 phút trên mọi
  máy tính bảng thì bcrypt thành nút thắt.
* **`find_refresh` khoá dòng** (`with_for_update`). Hai request refresh cùng lúc trên một token phải có
  đúng một cái thắng.

### Cookie httpOnly

Token nằm trong cookie `httpOnly`, **không trả trong body** — JavaScript của trang không đọc được thì
một lỗ XSS cũng không lấy được token. Refresh có `Path=/v1/auth` nên request thường không mang nó theo.

Cái giá: cookie tự đi kèm mọi request, tức mở cửa cho **CSRF**. `SameSite=lax` chặn được — **chỉ khi FE
và BE cùng site** (qua reverse proxy chung domain). FE khác origin thì phải `SameSite=none`, lá chắn của
trình duyệt mất, và lúc đó **bắt buộc thêm CSRF token**. Chưa làm vì chưa chốt FE deploy thế nào.

Cookie cũng buộc CORS phải `allow_credentials=True` và **không được** `allow_origins=["*"]` — trình
duyệt từ chối cặp đó rồi im lặng không gửi cookie. Origin khai ở `MES_CORS_ORIGINS`.

### Phân quyền — **#26 đã chốt**, xem BRD §9b

**Sáu phòng ban**, mỗi phòng một step. Kho (0) và Nhập kho (5) là **hai** phòng riêng. Đóng thùng thuộc
phòng Sản xuất. Mỗi phòng có Leader và Member — **hiện quyền y hệt nhau**, tách sẵn để sau siết không
phải sửa dữ liệu tài khoản.

| Phòng ban | Step của mình | Step 4 · Sản xuất | Step khác |
|---|---|---|---|
| Kho xuất · Setup · QC · Kho nhập | Full | **View** *(gồm cả Đóng thùng)* | — |
| **Bàn team leader** | Full | **FULL** (kể cả Đóng thùng) | — |
| Sản xuất | Full | *(chính nó)* | — |
| **PLANNER** | **Full mọi step** | Full | Full |

`Bảng đang chạy` là ngoại lệ: **mọi phòng ban đều xem được**, vì nó là bảng tổng quan của cả xưởng.

**13 vai** = 6 phòng × 2 cấp + PLANNER, **sinh ra từ** bảng quyền trong
`common/security/permissions.py` chứ không gõ tay — thêm phòng ban thì danh sách tự dài ra:

```
WAREHOUSE_OUT_LEADER/MEMBER · SETUP_* · QC_* · WAITING_* · PRODUCTION_* · WAREHOUSE_IN_* · PLANNER
```

Một người giữ được nhiều vai (`roles` là mảng) — lúc đó lấy **mức cao nhất**.

Luật tách khỏi nơi thi hành, đúng kiểu RBAC:

| Việc | Ở đâu |
|---|---|
| Bảng quyền *(vai → {trạm: mức})* | `common/security/permissions.py` — **một chỗ duy nhất** |
| Ra quyết định | `permission_for(roles, step_no)` → `full` / `view` / `None` |
| Thi hành | `Actor.require_step(step_no, level)` gọi ở router |
| Gán người vào vai | cột `app_user.roles[]`, đổi bằng SQL |

Router **không** tự so chuỗi vai. Muốn đổi luật thì sửa đúng `permissions.py`; muốn chuyển bảng
quyền xuống CSDL thì sửa ruột `permission_for`, 30 endpoint không đụng dòng nào.

`require_role` còn lại chỉ dùng cho **PLANNER** — việc điều độ không gắn với trạm nào.

**Đóng thùng không có trạm riêng**, nó nằm trong trạm 4. Nên `{4: FULL}` là ghi được cả
`production` lẫn `packing`, `{4: VIEW}` là xem được cả hai.

**Đã làm** (migration `0004_roles`, 42 test trong `tests/test_permissions.py`). Còn lại:
Leader kế thừa Member khi xưởng chốt hai cấp khác nhau ở đâu.

> Trạm lấy từ **thiết bị**, không lấy từ body. BRD §1b.3: *"mã QR chỉ nói MO nào, không nói bước nào"*.
> Để client tự khai trạm thì một máy giả được mọi trạm.

Mỗi sổ trạm là một bảng riêng, nên khi chốt #26 thì `GRANT` theo bảng là chuyện một buổi — đây chính là
lý do đã tách 14 sổ.

---

## 7. Giao dịch, khoá, và hai người bấm cùng lúc

**§10 #32 chưa chốt** (nhận đồng thời + đường lùi), nhưng phần chống đua phải làm ngay từ đầu.

| Tình huống | Cách chặn |
|---|---|
| Hai người cùng quét một MO ở hai trạm | `SELECT … FROM mo_round WHERE mo_id=… AND closed_at IS NULL FOR UPDATE` ở đầu mỗi service |
| Nhập kho thiếu → hai request cùng mở vòng mới | chỉ mục `mo_round_one_open` — request thứ hai vỡ, trả 409 |
| Chốt sổ SX hai lần | `RULE production_no_update` — lần hai không ghi được gì |
| Đóng thùng ghi đè số của Sản xuất | hai bảng riêng, không đụng nhau (§7b chạy song song) |
| Đầu đọc bắn hai lần | dedupe 2 giây ở `/v1/scan` |

**Mức cô lập:** `READ COMMITTED` (mặc định) là đủ, vì mọi bất biến đã có `CHECK` và chỉ mục duy nhất
canh. Không cần `SERIALIZABLE` — và không nên, vì nó đẩy việc thử lại sang phía ứng dụng.

---

## 8. Kiểm thử — chỗ quan trọng nhất của kế hoạch này

### Bắt buộc test trên **Postgres thật**

Hơn một nửa luật nghiệp vụ nằm trong `CHECK`, `EXCLUDE USING gist`, `RULE`, chỉ mục duy nhất một phần.
SQLite **không có** những thứ đó. Test trên SQLite cho màu xanh mà không kiểm được gì — tệ hơn là không
test, vì nó tạo cảm giác an toàn giả.

Dùng `testcontainers-python` dựng một Postgres cho mỗi lần chạy, chạy đủ Alembic, mỗi test một
transaction rồi rollback.

### Bốn nhóm test

| Nhóm | Kiểm cái gì | Ví dụ |
|---|---|---|
| **Ràng buộc** | Mỗi `CHECK` **thật sự chặn** | ghi `qty_ok+qty_ng+qty_short ≠ target_qty` → phải nổ |
| **Luồng** | Kịch bản thật của xưởng | 10.000 → vòng 1 làm 9.000 → về Bàn team leader → vòng 2 đóng nốt → `COMPLETED` |
| **Đua** | Hai request song song | hai lần `POST /receipt/complete` chỉ một cái mở được vòng mới |
| **View** | Số của view khớp số tính tay | `v_step_total` = tổng các dòng `mo_step` cùng `step_no` |
| **Đăng nhập** | Xoay vòng refresh và bắt dùng lại | gửi lại refresh đã dùng → thu hồi cả chuỗi |

**Hiện có 59 test.** Ba file chạy được **không cần CSDL** (`test_mocode` · `test_config` ·
`test_cookies`), còn lại dựng Postgres thật bằng testcontainers.

`test_config.py` đáng nói: nó đo hạn của token THẬT rồi so lại cấu hình. Con số `15` trong
`access_ttl_minutes` không mang đơn vị — đơn vị nằm ở `timedelta(minutes=…)` bên `security.py`, và
không gì buộc hai chỗ đó khớp nhau. Gõ nhầm `days=` thì token sống 15 **ngày** mà tên biến vẫn ghi
`minutes`. Bốn test rẻ hơn hẳn một bộ phân tích chuỗi `"15m"`, mà chặn đúng thứ cần chặn.

### Chép sẵn 116 mục kiểm thử của demo

Demo hiện có **116 assertion** đã chạy xanh, phủ đúng những cái bẫy đã gặp: số âm, vòng lặp vô hạn, đếm
hai lần lô cuối, `steps[5]` của vòng cũ khoá hàng đợi Nhập kho, cột `Bắt đầu từ` đoán nhầm sau QC FAIL.
**Dịch sang pytest trước khi viết service** — đó là bản đặc tả chính xác nhất đang có, và nó đã từng bắt
được năm lớp lỗi thật.

---

## 9. Migration

1. `0001_init.py` — chép DDL của `DB-GON.md`: enum → 14 sổ + `scan_dedupe` → chỉ mục → trigger → view.
   Phần `CHECK`, `EXCLUDE`, `RULE`, `CREATE VIEW` viết bằng `op.execute()` nguyên văn SQL, **không** cố
   diễn đạt qua API của Alembic — SQL gốc dễ đối chiếu với tài liệu hơn.
2. `0002_seed.py` — 14 chuyền + danh mục lý do + 8 tài khoản mẫu. Đây là **dữ liệu hệ thống**, thuộc về
   migration, không phải script chạy tay. PIN **băm tại chỗ** bằng bcrypt, không dán chuỗi băm sẵn:
   bản đầu dán nhầm một chuỗi trông-như-bcrypt, mọi tài khoản seed không đăng nhập được, mà chỉ lộ ra
   khi gọi thật `/auth/login`.
3. `0003_refresh_token.py` — bảng lưu refresh, thêm khi làm xoay vòng token.
4. `0004_roles.py` — đổi `app_user.roles` từ 7 vai phẳng sang 13 vai RBAC (§6).
5. Về sau mỗi thay đổi một file, **không sửa file đã chạy production**.

### `--autogenerate` BỊ CHẶN — và vì sao

`env.py` từ chối chạy `alembic revision --autogenerate`. Không phải để cho khắt khe:
**ở dự án này nó sinh ra lệnh sai.**

Đo thật ngày 2026-09-15 — chạy autogenerate trên CSDL đang đúng, không sửa gì:

```
18 dòng op.drop_index / op.drop_constraint, gồm:
   mo_round_one_open        chặn một MO có hai vòng cùng mở
   seg_one_open             chặn một chuyền có hai đoạn cùng mở
   refresh_token_con_song   chỉ mục tra token còn hiệu lực
   mo_step_round_id_step_no_key · hourly_output_..._key  …
```

Nguyên nhân: các thứ đó tạo bằng **SQL thô** trong `0001_init.py`, model không khai
lại. Autogenerate nhìn model, không thấy, kết luận là thừa. Ba cái đầu là ràng buộc
**giữ dữ liệu đúng**, không phải tối ưu tốc độ.

File sinh ra trông rất bình thường — 18 dòng `drop_index` lẫn giữa nhau, review lướt
là cho qua, chạy xong mới biết. Nên chặn ở gốc, kèm câu chỉ đường:

```
$ alembic revision --autogenerate -m "abc"
[alembic] --autogenerate bị chặn ở dự án này.
  Dùng:  ./run.sh mig-new "mo ta thay doi"   rồi tự viết op.execute(...).
```

Thoát với mã 1 nên CI bắt được. `upgrade`, `downgrade`, `revision` (không cờ) và
`command.upgrade()` mà `tests/conftest.py` gọi thì **không** bị đụng — đã kiểm cả bốn.

> Muốn autogenerate dùng được thì phải khai đủ 18 chỉ mục/ràng buộc vào
> `__table_args__` của model. Riêng `EXCLUDE USING gist` thì SQLAlchemy không diễn
> đạt được, nên dù có làm vẫn còn ngoại lệ. Không đáng.

**`alembic.ini` phải THUẦN ASCII.** `configparser` đọc file đó bằng bảng mã hệ thống (cp1252 trên
Windows), nên một chữ tiếng Việt trong đó làm alembic gãy ngay lúc khởi động.

**`env.py` không được ghi đè `sqlalchemy.url` mà người gọi đã đặt.** `tests/conftest.py` trỏ alembic vào
Postgres tạm của testcontainers; ghi đè bằng `settings` thì test chạy migration lên CSDL thật của máy.

**Quy tắc vàng:** view và trigger phải `CREATE OR REPLACE` được. Đổi view nào thì migration mới định
nghĩa lại nguyên cái view đó — đừng vá từng mảnh.

---

## 10. Vận hành

| Việc | Cách làm |
|---|---|
| Chạy | `gunicorn -k uvicorn.workers.UvicornWorker -w 4` · pool 5 kết nối mỗi worker |
| Cấu hình | `pydantic-settings`, gom theo nhóm — xem dưới. Không có secret trong repo |
| Công cụ | `uv` (venv + `uv.lock`) · `run.sh` thay `make` · `ruff` soát code |
| Log | JSON một dòng một bản ghi, có `request_id` · `mo_code` · `station` · `actor` |
| Healthcheck | `/healthz` (sống) và `/readyz` (chạm được DB) |
| Migration lúc deploy | **job riêng chạy trước**, không chạy trong lúc app khởi động — bốn worker cùng migrate là hỏng |
| Sao lưu | `pg_dump` hằng đêm + WAL archiving. **Thử phục hồi mỗi tháng**, sao lưu chưa phục hồi thử thì chưa phải sao lưu |
| Theo dõi | đếm lỗi 4xx/5xx theo endpoint; cảnh báo khi `/v1/scan` bắt đầu trả lỗi nhiều — đó là dấu hiệu đầu đọc hoặc mạng xưởng có vấn đề |

### Cấu hình gom theo NHÓM

Mỗi nhóm một lớp có tiền tố riêng, tương đương `registerAs('database', …)` của `@nestjs/config`:

```
MES_DATABASE_*  →  settings.database.url        MES_COOKIE_*  →  settings.cookie.secure
MES_JWT_*       →  settings.jwt.secret          MES_CORS_*    →  settings.cors.origins
MES_SCAN_*      →  settings.scan.dedupe_seconds
```

Thứ tự ưu tiên: **biến môi trường thật > `.env` ở gốc dự án > mặc định trong code**. Nên production
không cần `.env` — đặt thẳng biến môi trường là được, đúng như `docker-compose.yml` đang làm.

`database.url` và `jwt.secret` **không có mặc định**: thiếu là app từ chối khởi động kèm câu chỉ rõ
thiếu biến nào. Cho chúng một mặc định thì quên `.env` sẽ không báo gì — app cứ chạy, nối nhầm CSDL,
hoặc ký token bằng khoá ai đọc repo cũng biết.

`docker-compose.yml` **có lên git nên không chứa giá trị bí mật nào** — mọi thứ nhạy cảm đọc từ `.env`
bằng `${BIEN:?câu nhắc}`, thiếu thì compose dừng ngay.

> Secret đã lọt vào lịch sử git thì coi như hỏng vĩnh viễn: phải **đổi cái mới**, không phải chỉ xoá
> dòng đó đi.

### Neo đường dẫn, đừng tin thư mục đang đứng

`alembic`, `pytest`, `uvicorn` hay được gọi từ những chỗ khác nhau. `env_file=".env"` trần thì lúc thấy
lúc không — và khi không thấy, app **im lặng** dùng giá trị mặc định. Neo vào vị trí file:

```python
ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = ROOT / ".env"
```

---

## 11. Thứ tự làm

| Đợt | Làm gì | Xong khi | |
|---|---|---|---|
| **0 · Móng** | Dự án, Docker, Alembic, `/healthz` · `/readyz` | `docker compose up` là có DB đủ bảng + view | ✅ |
| **1 · Luật** | `test_constraints.py` cho **mọi** `CHECK`/`EXCLUDE`/`RULE` | Mỗi ràng buộc có ít nhất một test chứng minh nó chặn | ✅ 20 test |
| **2 · Lõi vòng chạy** | `round` · `scan` · `warehouse` · `qc` · bước | Chạy trọn 6 trạm bằng API, kể cả QC FAIL về Kho | ✅ |
| **3 · Sản xuất** | chuyền · chốt sổ SX · đóng thùng · nhập kho · vòng lặp Bàn team leader | Kịch bản 9.000 + 1.000 xanh | ✅ 12 test |
| **4 · Màn hình** | `board` · `trace` · `hourly` đọc từ view | FE thay dữ liệu giả bằng API thật | ✅ |
| **5 · Siết** | Xác thực · refresh token · cookie · log · dedupe quét | Chạy thử một ca thật ở xưởng | ~ |

**Còn lại của đợt 5**, theo thứ tự nên làm:

1. **CSRF token** — chỉ cần khi chốt FE chạy khác origin với BE (xem §6).
2. **Test đua thật** — hiện chưa có test nào bắn hai request song song. Chỗ đáng lo nhất:
   hai người cùng `POST /receipt/complete`, và hai máy cùng `POST /auth/refresh`.
3. **`board/repository.py`** — mọi câu SELECT từ view còn nằm trong `board/service.py`,
   ngoại lệ duy nhất của luật "SQL chỉ nằm trong repository".
4. **CI** — chạy `./run.sh lint` và `./run.sh test` trên mỗi lần đẩy code.
5. **Chạy thử một ca thật ở xưởng.**

---

## 12. Ba câu phải chốt trước khi đụng tới phần tương ứng

| # | Câu hỏi | Chặn phần nào |
|---|---|---|
| ~~**#36**~~ | ~~Mã MO do hệ thống cấp hay lấy từ ERP?~~ | **Đã chốt 2026-09-15 — lấy từ ERP.** Đã bỏ `POST /mos/batch` và hàm sinh mã liền số. Mã vào hệ thống qua nhập tay hoặc `POST /mos/import` |
| ~~#26~~ | ~~Phân quyền siết tới đâu?~~ | **Đã chốt 2026-09-14** — BRD §9b. Còn lại là việc code, xem §6 |
| **#40** | Bỏ in ở Kho thì QR dán lên hàng từ đâu? | Không chặn code, nhưng **chặn chạy thật**: không có tem thì sáu trạm không quét được gì |
| **#38** | Đóng thùng có cần ô nhập SL? | `packing_service` — bỏ được thì `qty_packed` thành cột tính từ `production.qty_ok`, bớt một ô nhập và một trigger |

---

## 13. Những thứ **không** làm

- **Không** viết lại luật của DB bằng Python cho "chắc ăn". Hai nơi giữ luật là hai nơi để lệch nhau.
- **Không** cache số dẫn xuất (`qty_done`, tỷ lệ phế…) khi chưa đo thấy chậm. View chạy được thì cứ view.
- **Không** soft-delete. §4A đã chốt: sai thì `CANCELLED` kèm lý do, không xoá.
- **Không** cho client gửi timestamp.
- **Không** tạo abstraction cho "sau này đổi CSDL". Sẽ không đổi.
- **Không** gộp nhiều thao tác vào một endpoint "tiện" — mỗi thao tác của người vận hành là một endpoint,
  một transaction, một dòng nhật ký.

---

_v1.1 — 2026-09-14. Đã đối chiếu với mã nguồn: 30 endpoint · 16 bảng · 59 test xanh._
_Căn cứ `BRD-v2-chot.md` v2.20 và `DB-GON.md` v2.4. Cập nhật khi hai tài liệu đó, hoặc mã nguồn, đổi._
