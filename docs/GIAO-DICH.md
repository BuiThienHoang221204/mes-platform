# Giao dịch trong backend MES — dùng ở đâu, làm gì

> 2026-09-14 · Mã nguồn `mes-backend/` · 106 test xanh
> Số liệu trong tài liệu này **đo bằng cách chạy thật**: nghe mọi câu SQL đi xuống
> Postgres khi đi trọn một MO qua sáu trạm, không phải suy từ code.

---

## Tóm tắt

Một lần bấm nút ở xưởng = **2 đến 6 câu ghi** trên **2 đến 5 bảng**, cộng một khoá dòng.
Giao dịch là thứ khiến người vận hành và cơ sở dữ liệu cùng gọi đó là **một** việc.

Ranh giới nằm ở **service**, đánh dấu bằng `@transactional`. Router không mở giao dịch,
không chạm CSDL.

---

## 1. Mỗi thao tác thực sự ghi những gì

Đo trên một MO đi trọn luồng (`M195473`):

| Thao tác | Khoá dòng | Câu ghi | Bảng bị ghi |
|---|---|---|---|
| Tạo MO | — | 2 | `manufacturing_order`, `mo_event` |
| Submit | — | 3 | `manufacturing_order`, `mo_round`, `mo_event` |
| Quét QR (mỗi trạm) | 1 | 3–4 | `mo_step`, `scan_dedupe`, `mo_event` |
| Kho xuất bàn giao | 1 | 2 | `warehouse_out`, `mo_event` |
| QC đạt | 1 | 2 | `qc_result`, `mo_event` |
| Gán chuyền | 2 | 2 | `line_segment`, `mo_event` |
| Cho chuyền chạy | 2 | 3 | `line_segment`, `mo_event` |
| Ghi sản lượng giờ | 1 | 2 | `hourly_output`, `mo_event` |
| Bắt đầu / kết thúc đóng thùng | 1 | 2 | `packing`, `mo_event` |
| Chốt sổ sản xuất | 2 | 4 | `line_segment`, `production`, `mo_step`, `mo_event` |
| **QC không đạt** | 1 | **5** | `qc_result`, `mo_round` (đóng), `mo_step`, `mo_round` (**mở vòng mới**), `mo_event` |
| **Nhập kho thiếu SL** | 2 | **6** | `mo_step`, `warehouse_in`, `mo_round` (đóng), `mo_round` (**mở mới**), `mo_step`, `mo_event` |
| Nhập kho đủ SL | 2 | 5 | `mo_step`, `warehouse_in`, `manufacturing_order`, `mo_round`, `mo_event` |

Hai dòng in đậm là hai chỗ đắt nhất — chúng **đóng vòng cũ và mở vòng mới** trong cùng
một lần bấm.

---

## 2. Giao dịch làm ba việc

### 2.1 Nguyên khối — hỏng giữa chừng thì không còn dấu vết

Lấy *QC không đạt* làm ví dụ. Nếu không có giao dịch và tiến trình chết sau câu ghi thứ 3:

- `qc_result` đã có kết quả FAIL ✓
- `mo_round` vòng 1 **đã đóng** ✓
- `mo_round` vòng 2 **chưa mở** ✗

MO đó biến khỏi mọi màn hình — bảng đang chạy và hàng chờ các trạm đều lọc theo
`closed_at IS NULL`. Không ai quét được nó, mà §4A đã khoá cứng sau Submit nên cũng không
sửa được. Chỉ còn cách vào CSDL gõ SQL tay.

Với giao dịch: `ROLLBACK` đưa về đúng trạng thái trước khi bấm. Người ở xưởng bấm lại.

### 2.2 Giữ cho chiến lược "luật nằm trong CSDL" đứng được

BE-PLAN nguyên tắc ①: luật nằm trong `CHECK` / trigger / `RULE`, backend **ghi rồi dịch
lỗi** chứ không kiểm trước. Ví dụ trigger `production_balances` chặn *đạt + hỏng + thiếu ≠
mục tiêu vòng*.

Thao tác chốt sổ ghi theo đúng thứ tự này (đo được):

```
1. UPDATE line_segment      ← đóng mọi chuyền còn mở
2. INSERT production        ← trigger production_balances nổ Ở ĐÂY
3. INSERT mo_event
4. UPDATE mo_step
```

Trigger nổ ở câu **thứ 2 trên 4** — câu 1 đã ghi xong. Không có giao dịch thì mọi chuyền
đã bị đóng, mà sổ sản xuất thì chưa có: vòng chạy kẹt ở trạng thái không màn hình nào mô
tả được.

`CHECK` và trigger chỉ bảo vệ được **một câu lệnh**; thứ bảo vệ **cả thao tác** là giao
dịch. Bỏ nó đi thì mọi luật phải chuyển lên Python và kiểm trước khi ghi — tức bỏ luôn
nguyên tắc ①.

### 2.3 Khoá dòng — hai người bấm cùng lúc thì xếp hàng

Khoá dòng (`SELECT … FOR UPDATE`) **chỉ sống bên trong một giao dịch** và nhả ngay lúc
commit. Có bốn chỗ khoá trong toàn bộ source:

| Khoá gì | Ở đâu | Chống cái gì |
|---|---|---|
| Vòng đang mở của một MO | `round/repository.lock_open_round` | hai người thao tác cùng một MO |
| Đoạn chuyền đang mở | `production/repository` (2 hàm) | bấm *dừng* và bấm *chạy* cùng lúc trên một chuyền |
| Dòng refresh token | `auth/repository.find_refresh` | hai tab cùng làm mới phiên |

Vì sao cần: nhiều thao tác có dạng **đọc → quyết định → ghi**.

```python
p = progress(db, mo.id)                                    # đọc: còn thiếu bao nhiêu
if p.qty_remain <= 0: raise DomainError(...)               # quyết định
round_repo.open_round(db, target_qty=p.qty_remain, ...)    # ghi
```

Giữa dòng đọc và dòng ghi, nếu người khác vừa đóng thùng thêm 500 cái thì `qty_remain` đã
cũ — vòng mới mở ra với mục tiêu sai, và **sai lặng lẽ**. Khoá khiến người thứ hai đợi tới
khi người thứ nhất commit rồi mới đọc.

---

## 3. Đặt ở đâu — `@transactional` ở service

```python
@transactional
def handover(db, *, code, actor_id):
    _, rnd = round_service.lock_round(db, code)   # khoá
    ...                                           # kiểm + ghi
```

Tương đương `@Transactional()` của NestJS/Spring với propagation **REQUIRED**: hàm được gọi
từ trong một giao dịch đang chạy thì **nhập vào**, không mở cái mới.

### 3.1 Vì sao không đặt ở router

* **Khoá phải nằm chung giao dịch với phần ghi.** Tách ra thì khoá nhả trước khi ghi xong.
* **Phạm vi là quyết định nghiệp vụ.** `handover_batch` gọi `handover` 100 lần trong MỘT
  giao dịch (§7A: *một mã hỏng thì cả lô không lệnh nào được giao*). Cùng một `handover`,
  hai ranh giới khác nhau — chỉ service biết.
* **Router không chạm CSDL** nên không thể lỡ mở một giao dịch chỉ-đọc rồi làm service
  tưởng mình đang lồng.

### 3.2 Vì sao không đặt ở repository

Repository làm **một** việc trên **một** bảng. `event_repo.log` không có cách nào biết nó
là câu ghi cuối của một chuỗi hay một việc lẻ. Để nó tự commit thì *QC không đạt* thành
năm giao dịch rời — chính là kịch bản §2.1.

---

## 4. Hiện trạng: 19 hàm có, 15 hàm không

`@transactional` đánh dấu **điểm vào của một thao tác nghiệp vụ**, không phải "hàm nào
chạm CSDL".

### 4.1 Có (19)

| Module | Hàm |
|---|---|
| `mo/` | `create` · `submit` · `cancel` |
| `scan/` | `scan` |
| `warehouse_out/` | `handover` · `handover_batch` |
| `qc/` | `qc_decide` |
| `production/` | `assign_line` · `line_start` · `line_hold` · `close_production` · `add_hourly` |
| `packing/` | `packing_start` · `packing_finish` |
| `warehouse_in/` | `complete` |
| `auth/` | `login` · `logout` · `_rotate` · `_revoke_chain` |

17 hàm đầu là điểm vào router gọi. Hai hàm cuối là private — xem §5.2.

### 4.2 Không (15), chia bốn nhóm

| Nhóm | Hàm | Vì sao |
|---|---|---|
| **Chỉ đọc** | `board/`: `running_board` · `queue` · `station_counts` · `trace` | đọc thì không có gì để commit hay huỷ |
| **Không chạm CSDL** | `reports/shift.bins_of` | hàm thuần, không nhận `db` — gắn vào là hỏng |
| **Nội bộ** | `round/`: `lock_round` · `progress` · `required_sec_for` · `open_first_round` · `open_next_round` · `close_round_completed` · `step_service.guard_can_accept` · `step_service.accept` | luôn được gọi từ trong một điểm vào đã mở giao dịch |
| **Ngoại lệ** | `auth/refresh` | xem §5.2 |

---

## 5. Ba chỗ đặc biệt — đọc kỹ trước khi sửa

### 5.1 `lock_round` KHÔNG ĐƯỢC gắn `@transactional`

```python
def lock_round(db, code) -> tuple[ManufacturingOrder, MoRound]:   # ← không decorator
    mo = mo_repo.get_mo(db, code)
    return mo, round_repo.lock_open_round(db, mo.id)              # SELECT … FOR UPDATE
```

Gắn vào thì nó tự mở giao dịch, lấy khoá, rồi **commit ngay khi trả về** — khoá nhả trước
cả khi service kịp ghi gì. Vẫn chạy, test vẫn xanh, nhưng chống đua thành vô nghĩa.

Khoá và phần ghi phải nằm trong **một** `@transactional` ở tầng trên nó.

### 5.2 `auth/refresh` cố ý KHÔNG có decorator

Phát hiện refresh token bị dùng lại thì phải thu hồi cả chuỗi **rồi mới** báo lỗi. Nhưng
câu `raise` báo lỗi lại rollback chính giao dịch chứa việc thu hồi — kẻ trộm vẫn còn đường
vào, mà thông báo thì nói *"đã thu hồi N phiên"*.

Nên tách thành **hai** đơn vị công việc:

```python
def refresh(db, *, refresh_raw):                  # ← không @transactional
    pair = _rotate(db, refresh_raw)               # @transactional
    if pair is not None:
        return pair
    n = _revoke_chain(db, refresh_raw)            # @transactional — COMMIT
    raise Forbidden(f"… đã thu hồi {n} phiên …")  # ném NGOÀI giao dịch
```

Chỗ tinh tế: **việc phát hiện nằm chung giao dịch với việc xoay vòng**, dưới cùng một
lần khoá dòng. `_rotate` trả `None` thay vì ném, để không tự huỷ giao dịch của mình.

Tách phát hiện ra thành một giao dịch riêng thì mở ra một khe hở: hai request cầm cùng
một token đều qua được bước kiểm rồi **cùng** xoay vòng — phát hai cặp token hợp lệ từ
một refresh. Bản đầu của chính đoạn này mắc đúng lỗi đó.

Đo thật, đường bình thường chỉ còn **một** lần khoá:

```
refresh | 4 câu | SELECT refresh_token FOR UPDATE · SELECT app_user
                · INSERT refresh_token · UPDATE refresh_token
```

Giao dịch thứ hai chỉ chạy trên đường hiếm (phát hiện dùng lại).

### 5.3 `deps.current_actor` phải trả session về trạng thái sạch

Nó đọc bản ghi người dùng ở mỗi request, mà một câu `SELECT` thì SQLAlchemy **tự mở** giao
dịch. Không đóng lại thì `transaction()` ở service tưởng mình đang lồng trong giao dịch của
người khác và **không commit**. Vì vậy `current_actor` gọi `db.rollback()` ngay sau khi đọc
xong giá trị.

---

## 6. Cơ chế: `app/common/uow.py`

```python
@contextmanager
def transaction(db: Session):
    if _owned.get():          # 1. lồng trong transaction() khác → nhập vào
        yield
        return
    token = _owned.set(True)
    try:
        with (db.begin_nested() if db.in_transaction() else db.begin()):
            yield
    finally:
        _owned.reset(token)
```

Ba tình huống:

| | Khi nào | Làm gì |
|---|---|---|
| 1 | gọi lồng | nhập vào, **không** commit ở đây |
| 2 | session sạch | `BEGIN` … thoát êm thì `COMMIT`, ném lỗi thì `ROLLBACK` |
| 3 | session đã có giao dịch của người khác | `SAVEPOINT` — đơn vị công việc vẫn nguyên khối, commit cái ngoài để người mở quyết định |

Tình huống 3 là đường mà fixture test đi (mỗi test bọc sẵn một giao dịch rồi rollback).
Dùng `SAVEPOINT` thay vì nhập thẳng là có chủ ý: nhờ vậy hành vi *"hỏng giữa chừng thì huỷ
sạch"* **kiểm được bằng test**, chứ không phải tin lời.

---

## 7. Hai lỗi đã gặp — đừng lặp lại

| Lỗi | Triệu chứng | Vì sao test cũ không bắt |
|---|---|---|
| `current_actor` để hở giao dịch chỉ-đọc | **Mọi endpoint ghi trả 500**: *"A transaction is already begun on this Session"* | test gọi thẳng service, không đi qua tầng dependency |
| Thu hồi token bị chính câu `raise` rollback | Báo *"đã thu hồi 7 phiên"* nhưng token mới **vẫn dùng được** | test gọi service trần, không có giao dịch nào để rollback |

Điểm chung: **cả hai chỉ lộ ra khi đi qua HTTP thật.** Đó là lý do `tests/test_uow.py` và
`tests/test_deps.py` dùng session sạch thay vì fixture `db` chung.

---

## 8. Thêm code mới thì nhớ gì

1. Hàm service mà **router gọi** và **có ghi** → gắn `@transactional`.
2. Hàm chỉ đọc → **không** gắn.
3. Hàm nội bộ được service khác gọi → **không** gắn (REQUIRED đã lo), trừ khi cố ý tách
   thành đơn vị công việc riêng như §5.2.
4. Gọi `lock_round` thì phải đang ở trong một `@transactional`.
5. Router **không** được gọi `_repo.*` trước khi gọi service — mở giao dịch chỉ-đọc là làm
   service tưởng mình đang lồng.
6. Cần "ghi cái này rồi ném lỗi" → tách hai hàm, đừng ghi rồi `raise` trong cùng một giao dịch.

---

## 9. Test nào canh cái gì

| File | Canh |
|---|---|
| `tests/test_uow.py` | service tự commit *(kiểm bằng kết nối khác)* · lỗi giữa chừng không ghi gì · gọi lồng không mở giao dịch mới · `handover_batch` nguyên khối theo §7A |
| `tests/test_deps.py` | `current_actor` trả session về trạng thái sạch |
| `tests/test_auth.py` | dùng lại refresh thì **cả chuỗi** chết — bao gồm token mới |

Cả `test_uow.py` lẫn `test_deps.py` đã được kiểm ngược: gỡ bản sửa ra thì chúng đỏ.
