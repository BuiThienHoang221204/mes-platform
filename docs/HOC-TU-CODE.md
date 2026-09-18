# Học từ code — sổ tay hỏi đáp

> Sổ ghi những thứ **không đọc ra được từ code**, chỉ hiện ra khi hỏi "vì sao lại viết thế".
> Mỗi mục là một câu hỏi, tự đứng được, không cần đọc mục trước.
>
> **Không dán code vào đây** — code dán vào tài liệu là code sẽ cũ đi. Thay vào đó mỗi mục có
> link kèm **khoảng dòng chính xác**, bấm vào là mở đúng chỗ trong `mes-backend/`.
> Số dòng được dò bằng script và kiểm ngược lại, không gõ tay.
>
> **Thêm mục mới:** đánh số tiếp, đừng chèn vào giữa — số mục được trích dẫn ở chỗ khác.
> Giữ đủ ba phần: **Ngắn gọn** → **Xem code** → **Vì sao**. Khẳng định nào đo được thì
> **đo rồi dán kết quả vào**, đừng viết theo trí nhớ.
>
> **Code dịch chuyển thì số dòng lệch** — chạy lại script dò link (xem cuối file) là cập nhật.

| # | Câu hỏi | Chủ đề |
|---|---|---|
| [1](#1) | Transaction để làm gì, có gì mà phải bọc? | giao dịch |
| [2](#2) | Vì sao transaction nằm ở service, không ở router? | giao dịch |
| [3](#3) | Service nào cũng gắn `@transactional` sao? | giao dịch |
| [4](#4) | Vì sao `submit` không có `FOR UPDATE` mà `qc_decide` có? | chống đua |
| [5](#5) | `now()` và `clock_timestamp()` khác nhau chỗ nào? | thời gian |
| [6](#6) | Thứ tự SQL không khớp thứ tự dòng code? | SQLAlchemy |
| [7](#7) | `db.flush()` giữa hàm để làm gì? | SQLAlchemy |
| [8](#8) | Bỏ tầng repository, gộp vào service được không? | kiến trúc |
| [9](#9) | Cái bẫy: gọi service mà không commit gì cả | giao dịch |
| [10](#10) | RBAC — vì sao không gán quyền thẳng cho người? | phân quyền |
| [11](#11) | N+1 query là gì, tìm và sửa thế nào? | hiệu năng |
| [12](#12) | Khi nào viết ORM, khi nào viết SQL thô? `IN` hay `ANY`? | truy vấn |

---

<a id="1"></a>
## 1. Transaction để làm gì, có gì mà phải bọc?

**Ngắn gọn:** vì **một lần bấm nút = 2–6 câu ghi trên 2–5 bảng**. Transaction làm cho người
vận hành và CSDL cùng gọi đó là *một* việc.

**Xem code:** [`qc/service.py:36-69`](../mes-backend/app/modules/qc/service.py#L36-L69)<!--at: def qc_decide--> — hàm
`qc_decide`, nhìn thì thấy *một* hàm.

### Vì sao

Bấm nút *"QC không đạt"* một lần, SQL thật đi xuống Postgres:

```
1. INSERT qc_result        4. INSERT mo_round   ← MỞ VÒNG MỚI
2. UPDATE mo_round         5. INSERT mo_event
3. UPDATE mo_step
```

Chết sau câu 2 thì vòng cũ **đã đóng**, vòng mới **chưa mở**. MO biến khỏi mọi màn hình (đều
lọc `closed_at IS NULL`), không ai quét được, mà §4A đã khoá cứng nên không sửa được. Chỉ còn
cách gõ SQL tay.

Ba việc transaction làm:

1. **Nguyên khối** — hỏng giữa chừng thì `ROLLBACK`, không để lại nửa vời.
2. **Đỡ cho chiến lược "luật nằm trong CSDL"** — trigger chỉ chặn được *một câu lệnh*; thứ
   bảo vệ *cả thao tác* là transaction.
3. **Giữ khoá dòng** — khoá chỉ sống bên trong transaction, nhả lúc commit.

**Đọc sâu:** [docs/GIAO-DICH.md](GIAO-DICH.md) — bảng đo từng thao tác.

---

<a id="2"></a>
## 2. Vì sao transaction nằm ở service, không ở router?

**Ngắn gọn:** vì **khoá dòng và phần ghi phải nằm chung một transaction**, mà chỉ service mới
biết cặp đó gồm những gì.

### Xem code — đặt cạnh nhau là thấy ranh giới

| Mở ra | Là gì |
|---|---|
| [`warehouse_out/router.py:23-29`](../mes-backend/app/modules/warehouse_out/router.py#L23-L29)<!--at: def handover--> | Router `handover` — **3 dòng**: kiểm quyền → gọi service → dựng câu trả lời. Không transaction, không SQL |
| [`warehouse_out/service.py:27-41`](../mes-backend/app/modules/warehouse_out/service.py#L27-L41)<!--at: def handover--> | Service `handover` — `@transactional`, khoá, kiểm, ghi |
| [`warehouse_out/service.py:44-54`](../mes-backend/app/modules/warehouse_out/service.py#L44-L54)<!--at: def handover_batch--> | `handover_batch` — gọi `handover` 100 lần trong **một** transaction |
| [`common/uow.py:34-80`](../mes-backend/app/common/uow.py#L34-L80)<!--at: @contextmanager -> return wrapper--> | `transaction()` + `transactional` — cơ chế bên dưới |

### Vì sao — ba lý do, xếp theo sức nặng

**1. Khoá.** `lock_round` chạy `SELECT … FOR UPDATE`, khoá nhả lúc commit. Nếu router mở
transaction rồi service mở cái khác thì khoá nằm ở transaction này mà phần ghi nằm ở
transaction kia — khoá thành vô nghĩa.

**2. Phạm vi là quyết định nghiệp vụ.** Cùng một `handover`, hai ranh giới khác nhau: gọi lẻ
thì một mã một transaction; gọi qua `handover_batch` thì cả lô một transaction — §7A nói *một
mã hỏng thì cả lô không lệnh nào được giao*. Chỉ endpoint biết mình đang ở tình huống nào.

**3. Repository không đủ thông tin.** `event_repo.log` không biết nó là câu ghi cuối của một
chuỗi hay một việc lẻ.

### Cơ chế

Trong `uow.py`, hai dòng `if _owned.get(): yield; return` **chính là propagation REQUIRED** —
thứ khiến Nest/Spring đặt được transaction ở service. Gọi lồng thì nhập vào, không mở cái mới.

---

<a id="3"></a>
## 3. Service nào cũng gắn `@transactional` sao?

**Ngắn gọn:** không. **19 hàm có, 15 hàm không.** Nó đánh dấu **điểm vào của một thao tác
nghiệp vụ**, không phải "hàm nào chạm CSDL".

### Bốn nhóm không gắn

| Nhóm | Ví dụ | Vì sao |
|---|---|---|
| Chỉ đọc | `board/running_board` · `queue` · `trace` | đọc thì không có gì để commit |
| Không chạm CSDL | `reports/shift.bins_of` | hàm thuần, không nhận `db` — gắn vào là hỏng |
| Nội bộ | `round/open_next_round` · `step_service/accept` | luôn gọi từ trong một điểm vào đã mở |
| Ngoại lệ | `auth/refresh` | xem [GIAO-DICH.md §5.2](GIAO-DICH.md) |

**Xem code:** [`round/service.py:43-51`](../mes-backend/app/modules/round/service.py#L43-L51)<!--at: def lock_round--> —
`lock_round`, hàm **KHÔNG ĐƯỢC** gắn decorator. Để ý docstring nói rõ lý do.

### Vì sao

Gắn `@transactional` vào `lock_round` thì nó tự mở transaction, lấy khoá, rồi **commit ngay
khi trả về** — khoá nhả trước cả khi service kịp ghi gì. Vẫn chạy, test vẫn xanh, nhưng chống
đua thành vô nghĩa. Đây là kiểu sai **không có gì báo**.

---

<a id="4"></a>
## 4. Vì sao `submit` không có `FOR UPDATE` mà `qc_decide` có?

**Ngắn gọn:** `FOR UPDATE` khoá **dòng đang có**. Lúc Submit thì vòng 1 **chưa tồn tại** —
chính hàm đó tạo ra nó.

### Xem code — đặt cạnh nhau

| Mở ra | Là gì |
|---|---|
| [`mo/service.py:80-91`](../mes-backend/app/modules/mo/service.py#L80-L91)<!--at: def submit--> | `submit` — `get_mo` là SELECT thường, và vòng 1 **sinh ra** ở dòng `open_first_round` |
| [`round/repository.py:43-56`](../mes-backend/app/modules/round/repository.py#L43-L56)<!--at: def lock_open_round--> | `lock_open_round` — `.with_for_update()`, thứ `qc_decide` gọi qua `lock_round` |
| [`0001_init.py:95-96`](../mes-backend/app/db/migrations/versions/0001_init.py#L95-L96)<!--at: -- Mỗi đơn chỉ MỘT lượt đang mở +1--> | Chỉ mục `mo_round_one_open` — thứ gánh việc chống đua thay cho khoá |

### Đo thật

Hai luồng bấm Submit cùng lúc trên cùng một MO:

```
Người A: DomainError: M781227 đã Submit rồi
Người B: OK — Submit thành công
→ CSDL: 1 vòng · status = PROCESSING
```

Lần đó A đọc sau khi B commit nên bị chặn ngay ở cửa Python. Khe hẹp hơn thì chỉ mục ra tay —
ghi thẳng một vòng thứ hai vào CSDL, bỏ qua hết Python:

```
✅ UniqueViolation … "mo_round_one_open"
→ backend dịch thành: "MO này đã có một vòng đang chạy" · HTTP 409
→ vẫn đúng 1 vòng đang mở
```

### Hai cách chống đua, chọn khi nào

| | `FOR UPDATE` | Ràng buộc duy nhất |
|---|---|---|
| Cần gì | **dòng phải có sẵn** | không cần gì |
| Người sau | **đợi**, rồi đọc trạng thái mới | **bị từ chối** |
| Thông báo | chính xác, Python soạn | chung chung hơn, dịch từ tên ràng buộc |

Cái giá của `submit`: ở khe hẹp nhất người dùng nhận *"MO này đã có một vòng đang chạy"* thay
vì *"đã Submit rồi"*. Chấp nhận được — Submit là việc của một Planner ngồi một chỗ, không phải
sáu trạm bấm song song.

---

<a id="5"></a>
## 5. `now()` và `clock_timestamp()` khác nhau chỗ nào?

**Ngắn gọn:** `now()` = **giờ bắt đầu transaction**, không đổi suốt transaction.
`clock_timestamp()` = **giờ thật ngay lúc gọi**.

### Xem code — hai hàm cùng đóng một thứ, dùng hai giờ khác nhau

| Mở ra | Dùng gì | Đóng cái gì |
|---|---|---|
| [`round/repository.py:94-102`](../mes-backend/app/modules/round/repository.py#L94-L102)<!--at: def close_step--> | `now()` | bước (`mo_step`) |
| [`round/service.py:130-135`](../mes-backend/app/modules/round/service.py#L130-L135)<!--at: def _close_open_segments--> | `clock_timestamp()` | đoạn chuyền (`line_segment`) |
| [`0001_init.py:194`](../mes-backend/app/db/migrations/versions/0001_init.py#L194)<!--at: CONSTRAINT seg_ends_after_start--> | — | ràng buộc `seg_ends_after_start`, lý do phải khác |

### Vì sao khác

Đoạn chuyền đòi `ended_at > started_at`. Mở rồi đóng một đoạn trong **cùng một transaction**
mà dùng `now()` thì hai mốc **bằng nhau** → ràng buộc nổ. Đây là lỗi thật đã gặp lúc dựng dự
án, không phải giả định.

Đo trong `qc_decide` nhánh FAIL thấy cả hai cùng xuất hiện, đúng vai:

```
 7. SELECT now()               ← mốc đóng bước (mo_step)
 8. SELECT clock_timestamp()   ← mốc đóng đoạn chuyền (line_segment)
10. SELECT now()               ← mốc đóng vòng (mo_round)
```

**Và vì sao lấy giờ từ CSDL chứ không từ Python:** đồng hồ các máy lệch nhau thì
`submitted_at` không so được với `mo_step.opened_at` nữa — mà cả hệ này sống bằng cách trừ hai
mốc thời gian. Đổi lại một vòng đi về CSDL.

---

<a id="6"></a>
## 6. Thứ tự SQL không khớp thứ tự dòng code?

**Ngắn gọn:** đúng vậy. Gán thuộc tính chỉ đổi trong **bộ nhớ**; tới `flush()` SQLAlchemy mới
xếp câu lệnh **theo phụ thuộc khoá ngoại**, không theo thứ tự bạn viết.

**Xem code:** [`qc/service.py:58-65`](../mes-backend/app/modules/qc/service.py#L58-L65)<!--at: step2 = round_repo.get_step -> )--> — nhánh
FAIL. Code gọi `close_step` (bảng `mo_step`) **trước**, rồi mới `open_next_round` (bảng
`mo_round`).

SQL thật đi xuống thì ngược lại:

```
11. UPDATE mo_round     ← bảng cha đi trước
12. UPDATE mo_step      ← bảng con đi sau
```

### Vì sao

`close_step` chỉ gán `step.closed_at = …` vào bộ nhớ, chưa gửi gì. Tới `db.flush()` bên trong
`open_next_round`, SQLAlchemy gom hết thay đổi đang treo và xếp theo khoá ngoại — `mo_step`
trỏ về `mo_round` nên bảng cha đi trước.

**Hệ quả khi đọc log:** đừng mong log SQL khớp thứ tự dòng code. Muốn một câu ghi xảy ra
**đúng chỗ đó** thì phải `db.flush()` — xem mục 7.

---

<a id="7"></a>
## 7. `db.flush()` giữa hàm để làm gì?

**Ngắn gọn:** đẩy các thay đổi đang treo xuống CSDL **ngay tại dòng đó**, để lỗi nổ đúng chỗ.
Nó **không** commit.

### Xem code — hai mức, hai ý nghĩa khác nhau

| Mở ra | Mức | Vì sao |
|---|---|---|
| [`qc/service.py:47-49`](../mes-backend/app/modules/qc/service.py#L47-L49)<!--at: qc_repo.save_qc -> db.flush()  # CHECK--> | **Bắt buộc** | không flush thì `CHECK` nổ sau khi vòng mới đã mở, thông báo trỏ nhầm chỗ |
| [`0001_init.py:114-115`](../mes-backend/app/db/migrations/versions/0001_init.py#L114-L115)<!--at: CONSTRAINT qc_fail_needs_reason +1--> | — | ràng buộc `qc_fail_needs_reason` mà dòng flush kia đang đợi |
| [`mo/service.py:86-89`](../mes-backend/app/modules/mo/service.py#L86-L89)<!--at: mo.status = MoStatus.PROCESSING -> round_service.open_first_round--> | **Không bắt buộc** | `open_round` bên dưới cũng flush; ở đây chỉ để lỗi nổ đúng dòng |

### Vì sao

Ở `qc_decide` đây là nguyên tắc ①: không kiểm lại bằng Python mà **ghi rồi dịch lỗi** — nhưng
phải ghi *đúng lúc*. Biết phân biệt hai mức này thì mới biết chỗ nào được phép xoá.

---

<a id="8"></a>
## 8. Bỏ tầng repository, gộp vào service được không?

**Ngắn gọn:** nên giữ. Và một tiền đề cần chỉnh: **Nest cũng có repository** — `Repository<T>`
do TypeORM sinh ra. Thứ tương đương trong SQLAlchemy là chính `Session`.

### Xem code — hai đầu của lập luận

| Mở ra | Là gì |
|---|---|
| [`qc/repository.py:1-30`](../mes-backend/app/modules/qc/repository.py#L1-L30)<!--at: FILE--> | Repository **mỏng nhất** — cả file 20 dòng cho một hàm một dòng. Nhìn thì đúng là thừa |
| [`board/repository.py:1-30`](../mes-backend/app/modules/board/repository.py#L1-L30)<!--at: """Truy vấn cho các màn hình điều hành +29--> | `board/` — module cuối cùng có repository, và lý do vì sao phải có |
| [`round/repository.py:43-56`](../mes-backend/app/modules/round/repository.py#L43-L56)<!--at: def lock_open_round--> | `.with_for_update()` — một dòng, quên là không có gì báo |

### Vì sao vẫn giữ

**Đo:** 31 hàm repository, **0 hàm chết**, **14 hàm được ≥2 file gọi**:

```
common.log          9 file        round.close_step    4 file
round.get_step      5 file        packing.get_packing 4 file
mo.get_mo           4 file
```

Bỏ tầng này thì `get_step` thành 5 bản sao của cùng một câu `select()` ở 5 module.

**Lý do quyết định — bốn chỗ khoá dòng.** `.with_for_update()` quên là không lỗi, không test
đỏ — chỉ là hai người bấm cùng lúc cùng đi qua, ở nhà máy, vài tháng một lần. Repository giữ
cho cả hệ thống chỉ có **một** chỗ biết "khoá vòng đang mở".

**Bằng chứng từ chính source này.** Đã có lúc `board/` là module **duy nhất không có
`repository.py`** — và cũng là module duy nhất có **13 chỗ SQL thô nằm trong `service.py`**.
Không phải trùng hợp: bỏ chỗ để đặt câu truy vấn thì câu truy vấn nằm lại nơi nó được viết ra.

Sửa xong `board/` lộ thêm một thứ nữa. Hai câu SQL của hàng chờ — câu **liệt kê** và câu
**đếm badge** — trước nằm rời nhau, không gì buộc chúng khớp. Gom về repository thì cả hai
dựng từ cùng một `QUEUE_SQL`. Đây là loại lợi ích mà tầng repository mang lại nhưng không ai
nhìn thấy cho tới lúc gom: **badge và danh sách không thể lệch nhau được nữa.**

**Giá trị thật không phải trừu tượng, mà là neo tên và ý nghĩa.** `db.get(QcResult, round_id)`
nói *"tra một dòng"*. `get_qc(...) is None` nói *"vòng này chưa kiểm"*. Cái thứ hai là nghiệp vụ.

---

<a id="9"></a>
## 9. Cái bẫy: gọi service mà không commit gì cả

**Ngắn gọn:** chạy một câu `SELECT` trước khi gọi service, rồi quên `rollback()` → service
tưởng mình đang lồng trong transaction của người khác và **không commit**. Không lỗi, không
cảnh báo — dữ liệu chỉ đơn giản biến mất.

**Xem code:** [`common/deps.py:79-85`](../mes-backend/app/common/deps.py#L79-L85)<!--at: user = auth_repo.get_user_by_id -> return actor--> — dòng
`db.rollback()` cuối `current_actor` tồn tại **chỉ vì** lý do này. Chú thích ngay trên nó nói rõ.

### Vì sao

SQLAlchemy **tự mở transaction** ở câu lệnh đầu tiên. `transaction()` thấy `db.in_transaction()`
là True thì hiểu *"có người khác đang giữ, để họ quyết định commit"* — nhưng không có ai cả.

Bẫy này có thật. Script thử nghiệm dính ngay lần đầu: lấy `user_id` bằng một câu `SELECT`, quên
`rollback()`, rồi gọi `create` và `submit` — kết quả là `"Không có MO M462442 trong hệ thống"`,
vì MO vừa tạo chưa bao giờ được commit.

### Cách tránh

1. `deps.current_actor` gọi `db.rollback()` ngay sau khi đọc người dùng.
2. **Router không được chạm CSDL** trước khi gọi service.
3. Viết script hay test dùng session sạch thì nhớ `rollback()` sau mỗi câu đọc rời.

`tests/test_deps.py` canh đúng điều này — gỡ bản sửa ra là test đỏ.

---

<a id="10"></a>
## 10. RBAC — vì sao không gán quyền thẳng cho người?

**Ngắn gọn:** người nhận **vai**, vai mới mang **quyền**. Hai lớp gán rời nhau nên đổi việc
của một người và đổi luật của cả phòng ban là hai thao tác không đụng nhau.

```
Người ──gán vai──► Vai ──gán quyền──► Quyền ──gác──► Hành động
```

### Xem code — ba tầng, ba file

| Mở ra | Vai trò |
|---|---|
| [`security/permissions.py:40-55`](../mes-backend/app/common/security/permissions.py#L40-L55)<!--at: # ══ Bảng quyền -> ] + [PLANNER]--> | `ROLE_PERMISSIONS` — **toàn bộ luật §9b.4**, và 13 vai *sinh ra* từ chính bảng này |
| [`security/permissions.py:76-94`](../mes-backend/app/common/security/permissions.py#L76-L94)<!--at: def permission_for--> | `permission_for` — **nơi ra quyết định** (PDP) |
| [`security/actor.py:36-50`](../mes-backend/app/common/security/actor.py#L36-L50)<!--at: def require_step--> | `Actor.require_step` — **nơi thi hành** (PEP) |

Router chỉ viết đúng một dòng: `actor.require_step(0)` — xem lại mục 2.

### Ánh xạ

| RBAC | Ở đây | Nằm đâu |
|---|---|---|
| Người | `app_user` | bảng CSDL |
| Vai | 13 vai (`QC_LEADER`, `WAITING_MEMBER`…) | `ROLES`, sinh ra từ bảng quyền |
| Quyền | cặp *(trạm, mức)* — `(4, VIEW)` | — |
| Gán người→vai | `app_user.roles[]` | CSDL, đổi bằng SQL |
| Gán vai→quyền | `ROLE_PERMISSIONS` | **code, một chỗ duy nhất** |
| Ra quyết định (PDP) | `permission_for` | `common/security/permissions.py` |
| Thi hành (PEP) | `Actor.require_step` | 8 router |

### Vì sao tách PDP khỏi PEP

Router chỉ **hỏi**, không tự suy luận. Muốn chuyển bảng quyền xuống CSDL thì sửa ruột
`permission_for` — 30 endpoint không đụng dòng nào.

**Đọc sâu:** [docs/KE-HOACH-PHAN-QUYEN.md](KE-HOACH-PHAN-QUYEN.md) — bốn bậc RBAC, tách trách
nhiệm giữa hai kho.

---

<a id="11"></a>
## 11. N+1 query là gì, tìm và sửa thế nào?

**Ngắn gọn:** N+1 là khi **số câu SQL tăng theo số dòng dữ liệu**. Không đọc code mà đoán ra
được — phải **tăng dữ liệu lên rồi đếm**.

### Cách tìm: tăng dữ liệu, đếm câu SQL

Gắn một bộ nghe vào SQLAlchemy rồi gọi cùng một hàm với lượng dữ liệu tăng dần:

```python
@event.listens_for(engine, "before_cursor_execute")
def nghe(conn, cursor, statement, params, context, executemany):
    if dang_dem:
        so_cau.append(statement)
```

Kết quả đo trên `board.trace` — cùng một MO, thêm dần số vòng chạy:

```
1 vòng →  10 câu SQL
2 vòng →  15 câu SQL  (+5)
3 vòng →  20 câu SQL  (+5)
4 vòng →  25 câu SQL  (+5)
```

**Đều đặn +5 mỗi vòng.** Đó là chữ ký của N+1. Đo cùng lúc các hàm khác để biết chỗ nào lành:

| Hàm | Kết quả | |
|---|---|---|
| `running_board` | 1 câu dù bao nhiêu MO | ✅ đọc view |
| `queue(n)` | 1 câu | ✅ |
| `mo.create` | 2 câu cho 10 MO | ✅ SQLAlchemy tự gộp `INSERT` |
| `station_counts` | 7 câu **cố định** | ⚠️ không phải N+1, nhưng lãng phí |

### Vì sao nó xảy ra

Code đọc rất xuôi tai — "mỗi vòng thì lấy các phần của nó":

```
for rnd in rounds_of(db, mo.id):
    steps_of(db, rnd.id)          ← 5 câu
    line_rows(db, rnd.id)         ←  cho MỖI
    hourly_of(db, rnd.id)         ←  vòng
    get_production(db, rnd.id)
    get_packing(db, rnd.id)
```

Không ai viết sai cả. Nó chỉ là **vòng lặp có truy vấn bên trong** — và điều đó không nhìn
thấy được cho tới khi có người đo.

### Cách sửa: đọc TRƯỚC, ghép SAU

Gom hết `round_id` lại, hỏi mỗi bảng **đúng một câu**, rồi mới dựng cây:

| Mở ra | Là gì |
|---|---|
| [`round/repository.py:128-143`](../mes-backend/app/modules/round/repository.py#L128-L143)<!--at: def steps_of_rounds--> | `steps_of_rounds` — bản theo lô, trả `dict[round_id, …]` |
| [`board/service.py:108-183`](../mes-backend/app/modules/board/service.py#L108-L183)<!--at: def trace--> | `trace` sau khi sửa — năm lời gọi nằm NGOÀI vòng lặp |

Điểm đáng học: hàm theo lô **trả `dict` chứ không trả `list`**. Người gọi tra thẳng
`steps.get(rnd.id, [])`, không phải tự nhóm lại — mà tự nhóm chính là chỗ dễ ghép nhầm dữ
liệu sang vòng khác.

```
5 + 5N câu  →  10 câu, cố định
4 vòng: 25 → 10      10 vòng: 55 → 10
```

### Thứ nảy ra ngoài dự tính

Gom SQL về `board/repository.py` mới lộ ra: câu **liệt kê** hàng đợi và câu **đếm badge**
trước nằm rời nhau, **không gì buộc chúng khớp**. Badge hiện 5, bấm vào ra 3 — không lỗi,
không test đỏ, chỉ có người ở xưởng thấy lạ.

Nay cả hai dựng từ một `QUEUE_SQL` duy nhất:

| Mở ra | Là gì |
|---|---|
| [`board/repository.py:175-201`](../mes-backend/app/modules/board/repository.py#L175-L201)<!--at: def queue_counts--> | `queue_counts` — đếm cả sáu trạm bằng MỘT câu, dựng từ `QUEUE_SQL` |

`station_counts`: **7 câu → 1**. Và badge với danh sách không thể lệch nhau được nữa.

### Phần quan trọng nhất: test chống tái phát

Sửa xong mà không có test thì vài tháng nữa ai đó thêm một dòng vào vòng lặp là quay lại
như cũ — **vẫn chạy đúng, chỉ chậm dần**, không ai biết.

| Mở ra | Là gì |
|---|---|
| [`tests/test_board.py:147-173`](../mes-backend/tests/test_board.py#L147-L173)<!--at: def test_trace_KHONG_hoi_them_khi_MO_co_nhieu_vong--> | Đếm SQL ở MO 1 vòng và 2 vòng, bắt bằng nhau |

Test này đã được **kiểm ngược**: đưa một truy vấn trở lại vào vòng lặp thì nó đỏ ngay.
Sửa một lỗi hiệu năng mà không kiểm ngược test thì không biết test có răng hay không.

Một chi tiết vấp phải lúc viết: lần đo đầu ra 11 câu, lần sau 10. Hoá ra fixture test bật
`autoflush`, nên lần gọi đầu kéo theo một câu ghi đang treo. Phải `db.flush()` trước khi đo.

### Nhớ gì khi viết code mới

1. **Vòng lặp có truy vấn bên trong** là dấu hiệu cần đo, không phải cần sợ — có khi N luôn
   bằng 1 thì chẳng sao.
2. Đo bằng cách **tăng dữ liệu**, không phải đọc code đoán.
3. Sửa xong thì **thêm test đếm SQL**, và kiểm ngược xem test có đỏ thật không.
4. Hàm theo lô nên trả `dict` khoá theo id, để người gọi khỏi tự nhóm.

---

<a id="12"></a>
## 12. Khi nào viết ORM, khi nào viết SQL thô? `IN` hay `ANY`?

**Ngắn gọn:** mặc định **ORM**; chuyển sang SQL thô chỉ khi ORM diễn đạt dài hơn hoặc
không diễn đạt nổi. Và lọc danh sách thì **ORM dùng `.in_()`, SQL thô dùng `= ANY()`**.

### Đo trước: hai kiểu chia nhau thế nào

**32 hàm ORM · 9 hàm SQL thô.** Chín cái đó không rải ngẫu nhiên:

| Hàm SQL thô | Vì sao |
|---|---|
| `board.running_rows` · `step_totals` · `mo_progress` | đọc **view** |
| `board.line_rows_of_rounds` | view + JOIN |
| `board.queue_rows` · `queue_counts` | JOIN, `UNION ALL`, `count()` |
| `scan.scan_remember` | `ON CONFLICT … DO UPDATE` |
| `scan.scan_seen_recently` | `make_interval()` |
| `round.close_step` | lấy `SELECT now()` từ CSDL |

Toàn bộ nằm ở hai module: `board/` và `scan/`. Chín module còn lại thuần ORM.

### Luật

> **Mặc định ORM.** Chuyển sang `text(...)` khi rơi vào một trong ba:
> 1. đọc **view**
> 2. **JOIN / gộp / `UNION`** nhiều bảng
> 3. thứ **riêng của Postgres** mà ORM viết dài hơn — `ON CONFLICT`, `make_interval`, hàm thời gian

### Xem code — ba ví dụ, ba tình huống

| Mở ra | Là gì |
|---|---|
| [`packing/repository.py:37-42`](../mes-backend/app/modules/packing/repository.py#L37-L42)<!--at: def packing_of_rounds--> | **ORM** — một bảng, lọc theo khoá, dùng `.in_(round_ids)` |
| [`board/repository.py:203-223`](../mes-backend/app/modules/board/repository.py#L203-L223)<!--at: def line_rows_of_rounds--> | **SQL thô** — đọc view `v_line_time` JOIN `line`; chỗ DUY NHẤT dùng `= ANY` |
| [`scan/repository.py:39-51`](../mes-backend/app/modules/scan/repository.py#L39-L51)<!--at: def scan_remember--> | **SQL thô** — `ON CONFLICT … DO UPDATE`, upsert của Postgres |

### Vì sao không gộp về một kiểu

**Hết về ORM** — phải khai 7 lớp model chỉ để đọc 7 view. Mà `EXCLUDE USING gist` và
chỉ mục một phần thì SQLAlchemy không diễn đạt nổi, nên dù có làm vẫn còn ngoại lệ.
Câu hàng đợi 4 dòng SQL sẽ thành hơn chục dòng `select().join().outerjoin()`.

**Hết về SQL thô** — vứt 32 hàm đang rất gọn, và **mất `.with_for_update()`**. Bốn chỗ
khoá dòng hiện là một lời gọi phương thức; thành chuỗi ký tự thì quên là không ai báo.
Xem [mục 8](#8) về giá trị của repository.

### `IN` hay `ANY` — đo trong SQL thô

| | Viết thế nào | Danh sách rỗng |
|---|---|---|
| `= ANY(:ids)` | truyền thẳng `{"ids": ids}` | **OK, 0 dòng** |
| `IN :ids` | phải thêm `.bindparams(sa.bindparam("ids", expanding=True))` | **ProgrammingError** |

Quên `expanding=True` thì báo `syntax error at or near "$1"` — không nhắc gì tới nguyên
nhân thật.

Danh sách rỗng là chuyện xảy ra thật: MO vừa tạo thì chưa có vòng nào, `line_rows_of_rounds`
nhận `[]`.

Bên ORM thì ngược lại — `.in_([])` được SQLAlchemy dịch thành `1 != 1`, an toàn sẵn. Nên
mỗi tầng dùng cái hợp với nó.

### Giới hạn 65.535 tham số

`IN` sinh **mỗi phần tử một tham số**, mà Postgres chỉ nhận tối đa 65.535 tham số một câu.
Đo thật:

```
IN     1 000 id  →  chạy được, 199 ms
IN    60 000 id  →  chạy được, 558 ms
IN    70 000 id  →  ❌ number of parameters must be between 0 and 65535

ANY    1 000 id  →  chạy được,  56 ms
ANY   60 000 id  →  chạy được, 213 ms
ANY  200 000 id  →  chạy được, 883 ms
```

`ANY` gói cả danh sách thành **một** tham số kiểu mảng nên không bao giờ chạm ngưỡng —
và ở 60.000 id còn nhanh hơn ~2,6 lần, vì Postgres khỏi phải phân tích 60 nghìn dấu `$n`.

Ở dự án này danh sách là **số vòng của một MO** — nhiều nhất chục cái, cách ngưỡng vài
nghìn lần. Nên `.in_()` vẫn là lựa chọn đúng: dễ đọc hơn.

> Nếu có ngày bạn định nhét vài chục nghìn id vào `IN`, cách đúng thường **không** phải
> đổi sang `ANY` mà là viết `JOIN` — để dữ liệu khỏi đi từ CSDL ra Python rồi lại nhét
> ngược vào CSDL.

### Nhớ gì

1. Viết ORM trước; thấy phải JOIN hay đọc view thì mới xuống SQL thô.
2. SQL thô chỉ được nằm trong `repository.py` — service và router không đụng.
3. Lọc danh sách: ORM `.in_()`, SQL thô `= ANY(:ids)`. Đừng đổi chéo.

---

## Giữ số dòng khỏi lệch

Code dịch chuyển thì mọi link ở trên trỏ sai. Hai script trong `mes-backend/tools/` lo việc đó:

```bash
python tools/docs_link.py     # dò lại vị trí thật, sửa mọi link trong docs/
python tools/docs_check.py    # kiểm ngược: link có nhảy đúng chỗ không
```

`docs_link.py` dò bằng cách khớp **tên hàm / dòng đầu và dòng cuối** của đoạn được trỏ tới,
nên đổi tên hàm là nó báo không tìm thấy — đúng lúc cần biết.

---

## Đọc thêm

| Tài liệu | Nội dung |
|---|---|
| [docs/GIAO-DICH.md](GIAO-DICH.md) | Giao dịch: dùng ở đâu, bảng đo từng thao tác, ba chỗ đặc biệt |
| [docs/KE-HOACH-PHAN-QUYEN.md](KE-HOACH-PHAN-QUYEN.md) | Phân quyền RBAC: mô hình, ma trận, cách triển khai |
| [mes-backend/BE-PLAN.md](../mes-backend/BE-PLAN.md) | Kiến trúc backend, bốn nguyên tắc nền |
| [demo/BRD-v2-chot.md](../demo/BRD-v2-chot.md) | Nghiệp vụ gốc — mọi §x trong code trỏ về đây |
| [demo/DB-GON.md](../demo/DB-GON.md) | DDL đầy đủ, 14 sổ + 2 bảng hạ tầng |
