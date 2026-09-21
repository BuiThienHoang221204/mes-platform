# Rà soát — polling, cache đọc, và đường đi của thay đổi

Câu hỏi mở đầu: *ba API đang hỏi lại liên tục có làm nghẽn máy chủ không?*

Trả lời ngắn: **không, ở quy mô này**. Nhưng khi soi đường đi của một thay đổi từ
lúc có người quét cho tới lúc nó hiện lên màn hình, lộ ra bảy lỗi **sai kết quả** —
năm cái đang chạy thật ngoài xưởng, hai cái còn lại nổ đúng lúc rời máy chủ tạm để
bật nhiều tiến trình.

Nặng nhất là A5: **đường đẩy SSE chưa từng giao được một tin nào**, mà mọi dấu hiệu
bên ngoài đều bình thường.

Ba chỗ suy đoán của tôi **đo ra là sai**, và đều sai theo hướng khác nhau:

| Tôi đoán | Đo được |
|---|---|
| `count_running` phải dựng cả view (§5.1) | Postgres cắt sạch — 0,095 ms, không sửa |
| Nhịp ghi nghiền nát cache (§3) | 54 vs 4 lượt ghi/phút → tỉ lệ chỉ lệch 1,3 điểm |
| `mark_affected` thiếu vài chỗ (§2/A4) | Nặng hơn nhiều: đường đẩy **chưa từng chạy** |

Đó là lý do §4.4 dựng bộ đếm và §4.12 dựng bộ mô phỏng — để lần sau khỏi đoán.

---

## 1 · Đang có gì

### 1.1 Ba API hỏi lại theo nhịp

| API | Hook | Nhịp | Ai xem |
|---|---|---|---|
| `GET /board/running` | `useRunning` | 10s | Bảng treo tường, bảng lệnh |
| `GET /board/overview` | `useOverview` | 10s | Màn điều độ |
| `GET /board/counts` | `useCounts` | 30s | Badge sidebar — **mọi** máy |

### 1.2 Hai API đã bỏ hỏi lại

`GET /board/queue/{station}` và `GET /board/at/{station}` đặt `staleTime: Infinity`,
chờ SSE đẩy `queue:changed` rồi mới nạp lại.

### 1.3 Tải ước tính

22 máy (18 tablet trạm + 2 bảng tường + 2 điều độ) ≈ **68 request/phút ≈ 1,1/giây**.

Postgres trên máy chủ trả phí xử lý mức này không cần nghĩ. Polling **không** phải
vấn đề. Phần còn lại của tài liệu nói về những thứ là vấn đề.

---

## 2 · Mười điểm đã tìm ra

Chia theo hậu quả, không theo độ khó.

### Loại A — sai kết quả

| | Điểm | Nổ khi nào |
|---|---|---|
| **A1** | `event_bus` giữ danh sách người nghe trong bộ nhớ MỘT tiến trình | Bật `-w > 1` |
| **A2** | `read_cache` cũng theo tiến trình → nhiều tấm bảng không biết nhau | Bật `-w > 1` |
| **A3** | SSE nối lại nhưng không nạp lại dữ liệu | **Đang nổ** |
| **A4** | `scan()` không báo cho trạm KẾ TIẾP | **Đang nổ** |
| **A5** | Event bus **chưa bao giờ** giao được tin tới SSE | **Đang nổ — nặng nhất** |
| **A6** | `_pending` dùng chung một `set()` cho mọi context | **Đang nổ** |
| **A7** | `/sse/{station}` nằm ngoài ma trận phân quyền §12.4 | **Đang nổ** |

**A1.** Tablet nối vào tiến trình B; người quét ở trạm khác rơi vào tiến trình A.
A phát thông báo, nhưng chỉ tới được ai đang nghe ở A. Với 4 tiến trình, xác suất
một thông báo tới đúng người ≈ 1/4. Không có lỗi nào hiện ra — màn hình chỉ đứng im.

**A2.** Người quét → tiến trình A xoá bảng của A. Màn hình hỏi lại → rơi vào tiến
trình C → C còn bảng cũ. Đúng thứ mà docstring của `read_cache.py` viết ra để tránh:
*"người vận hành sẽ quét lại lần hai vì tưởng máy không ăn"*. Quét lại lần hai ở MES
là sai số lượng và sai nhật ký.

**A3.** `createStationSSE` nối lại được, nhưng không báo cho ai. Cộng với
`staleTime: Infinity`, những event bay qua lúc đứt mạng là **mất hẳn**. Máy chỉ xem
không bao giờ tự phục hồi. → đã sửa, xem §4.

**A4.** Ban đầu tôi đoán vấn đề là *thiếu* `mark_affected` ở vài hàm. Rà kỹ thì sai —
thiếu hẳn là **vô hại** dưới thiết kế mặc-định-an-toàn (§5.3): không khai phạm vi thì
xoá sạch, đúng như bây giờ. Thứ nguy hiểm là khai **không đủ**.

Và có đúng một chỗ khai không đủ, ngay trong `scan()`:

| Hàng chờ | Điều kiện vào (`QUEUE_SQL`) | Ai tạo ra điều kiện đó |
|---|---|---|
| trạm 2 | có `mo_step` bước 1 | `scan(1)` |
| trạm 4 | có `mo_step` bước 3 | `scan(3)` |

`scan()` chỉ đánh dấu `station` và `station - 1`. Nên khi Setup quét nhận, lệnh **rơi
vào hàng chờ QC** nhưng tablet QC **không được báo** — và vì `queue` đặt
`staleTime: Infinity` lại không còn polling, màn hình đó đứng im cho tới khi có lý do
khác nạp lại. Cùng chuyện với Bàn team leader → Sản xuất.

Đây là lỗi **đang chạy thật**, không phải mìn chờ. → đã sửa, xem §4.6.

Ba trạm còn lại vào hàng chờ theo điều kiện khác (Setup đợi Kho bàn giao, Bàn team
leader đợi QC kết luận PASS, Kho nhập đợi đóng thùng xong) nên `scan()` ở trạm liền
trước **không** được đánh dấu chúng — hàm tạo ra điều kiện mới là hàm phải báo, và cả
ba đều đã báo đúng (`handover` → (0,1), `qc_decide` PASS → (2,3), `packing_finish` →
(4,5)).

`close_production` chỉ đánh dấu trạm 4 và **đúng**: §7b bắt Đóng thùng kết thúc SAU
chốt sổ, nên lúc chốt sổ lệnh chưa đủ điều kiện vào hàng chờ Kho nhập.

Hai hàm sản lượng giờ và hai hàm danh mục chuyền không đánh dấu gì, cũng **đúng**:
chúng không làm đổi hàng chờ hay danh sách đang-ở-trạm của bất kỳ trạm nào. Khi làm
§5.6 (SSE cho bảng) thì chúng sẽ cần đánh dấu phạm vi `board`.

**A5.** Đây là cái nặng nhất, và nó làm mọi phân tích phía trên phải đọc lại.

`subscribe_async` tra event loop **lúc phát tin** thay vì bắt **lúc đăng ký**:

```python
def _sync_bridge(data):
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return                    # ← rơi vào đây, mọi lần
```

Endpoint SSE là `async def` nên chạy TRÊN event loop. Nhưng mọi endpoint **ghi**
(`scan`, `handover`, `qc_decide`, …) là `def` thường, nên FastAPI chạy chúng trong
**threadpool** — ở đó không có event loop, `get_running_loop()` ném `RuntimeError`,
và hàm lặng lẽ trả về.

Đo trực tiếp:

```
emit() từ luồng threadpool  →  SSE nhận 0 event
emit() từ chính event loop  →  SSE nhận 1 event
```

Nghĩa là **SSE chưa từng đẩy được một tin nào trong lúc chạy thật**. Kết nối vẫn mở,
keepalive vẫn về đều, `/v1/sse/{station}` trả 200 — mọi dấu hiệu bên ngoài đều bình
thường. Chỉ có tin là không bao giờ tới.

Ghép với `staleTime: Infinity` và việc đã bỏ polling cho `queue`/`at`: màn hình trạm
chỉ đổi khi **chính máy đó** thao tác. Một tablet chỉ đứng xem thì không bao giờ thấy
việc mới.

Ba khối mã chết đi kèm — `_sync_to_async_bridge`, `_async_queues`, `_async_lock` —
không ai gọi, nhưng đọc qua thì trông đúng như đang lo chuyện này. Đó là lý do lỗi
sống lâu. Đã xoá.

**A6.** `_pending` khai `ContextVar(..., default=set())`. Mặc định của `ContextVar` là
**một vật thể dùng chung cho mọi context**. Một giao dịch đánh dấu xong rồi lỗi trước
khi đẩy sẽ làm bẩn vật thể ấy **vĩnh viễn** — mọi request sau khởi đầu với trạm thừa
trong tay và đẩy thừa mãi mãi. Đo được:

```
context MỚI, chưa đánh dấu gì  →  pending = {3}
```

### Loại B — chậm

| | Điểm | Chi tiết |
|---|---|---|
| **B1** | Mỗi request tốn 1 lượt tra `app_user` | Chạy TRƯỚC cache, nên "cache hit" vẫn chạm CSDL. Khoảng **một nửa** tổng số truy vấn |
| **B2** | Không chống dồn | 22 máy cùng trượt = 22 lượt truy vấn giống hệt |
| ~~B3~~ | ~~`count_running` dựng cả view để đếm~~ | **Đo rồi — không phải vấn đề.** Xem §5.1 |

`_store` của `read_cache` trước đây không bao giờ dọn — `offset` không chặn trên nên
số key chỉ có lên. → đã sửa, xem §4.

---

## 3 · Vì sao cache hiện tại không đủ

`read_cache` chống được **số máy**: 50 máy hay 500 máy thì vẫn một lượt truy vấn.
Đó là thiết kế đúng và nên giữ.

Tôi từng viết ở đây rằng nó **không** chống được **nhịp ghi**, và ca cao điểm sẽ
nghiền nát cache. **Đo rồi: sai.** Xem §4.12.

| | Nhịp ghi | Cache dùng lại được |
|---|---|---|
| Đầu ca | 54 lượt/phút | **63,7%** |
| Giữa ca | 4 lượt/phút | **65,0%** |

Nhịp ghi gấp **13 lần** mà tỉ lệ chỉ lệch 1,3 điểm. Thứ quyết định không phải `bump()`
mà là **TTL 5 giây gặp nhịp hỏi 10/30 giây**: một khoá chỉ được dùng lại khi có máy
khác vừa hỏi đúng nó trong 5 giây trước đó. Với 22 máy lệch pha nhau, con số rơi vào
khoảng 2/3 — gần như không phụ thuộc xưởng đang bận hay rảnh.

### Chia cache theo trạm giúp được ít hơn tưởng

Và vì thế, chia `_version` theo trạm càng ít giá trị hơn nữa — nó nhắm vào `bump()`,
thứ hoá ra không phải nút thắt. Ba lý do cũ vẫn đúng:

- `board:counts` là **một** key bao cả 6 trạm, mà đây lại là endpoint **mọi** máy đều
  hỏi. Chia theo trạm không cứu được nó.
- `board:queue:N` do SSE điều khiển. Khi trạm 5 ghi và cache trạm 3 bị xoá, **không ai
  hỏi tới cache trạm 3 cả** — xoá nhầm cũng vô hại.
- `board:running` và `board:overview` đổi theo gần như mọi lượt ghi, nên dù chia thế
  nào cũng vẫn phải dựng lại.

→ Thứ trả lại nhiều nhất là **chống dồn** (B2) và **bỏ lượt tra người dùng** (B1),
không phải chia phạm vi.

---

## 4 · Đã làm

### 4.1 SSE nối lại thì nạp lại — sửa A3

`src/services/sse.ts` thêm `onReconnect`, bắn trong `es.onopen` và **bỏ qua lần kết
nối đầu tiên** (lần đó React Query đã tự nạp khi mount).

`src/hooks/board/useSSE.ts` nối `onReconnect` vào đúng việc mà `onQueueChanged` làm.

**Cách thử:** mở tablet, chặn mạng ~10 giây bằng DevTools, trong lúc đó quét một lệnh
từ máy khác, rồi mở mạng lại. Hàng đợi phải tự đúng trong vài giây. Trước bản này thì
không.

### 4.2 Chống dồn — sửa B2

`read_cache.cached()` giờ có cổng: cùng một key mà cùng trượt thì chỉ **một** luồng
chạy `produce()`, các luồng còn lại chờ rồi dùng chung kết quả.

Dùng 64 cổng băm theo key chứ không phải một khoá mỗi key: số cổng cố định nên không
rò bộ nhớ. Hai key khác nhau trúng cùng cổng thì chỉ tuần tự hoá một nhịp — không sai
kết quả, và cũng là một cách hãm tự nhiên số truy vấn chạy song song.

Luồng đang chờ **không giữ kết nối CSDL**: `deps.current_actor` đã đóng giao dịch
chỉ-đọc của nó ngay sau khi đọc, nên kết nối đã trả về pool trước khi tới cache.

`_store` cũng có trần `MAX_KEYS = 512`, vượt thì dọn mục hết hạn trước, vẫn vượt thì
xoá sạch.

### 4.3 Bỏ lượt tra người dùng mỗi request — sửa B1

`deps.py` nhớ tạm `Actor` theo `sub`, mặc định 30 giây, chỉnh bằng
`MES_AUTH_ACTOR_CACHE_TTL` (0 = tắt hẳn).

**Đánh đổi phải biết:** khoá một tài khoản có hiệu lực chậm tối đa bằng TTL, và chậm
riêng ở **từng tiến trình**. Đường thoát là `deps.forget_actor(user_id)`; gọi
`forget_actor()` không tham số thì quên tất cả.

Chỉ nhớ trường hợp **thành công**. Tài khoản đã tắt ném lỗi trước khi kịp nhớ, nên
không có chuyện cache một câu trả lời sai.

### 4.4 Bộ đếm — để đo thay vì đoán

`GET /ops/cache-stats` (cần vai `PLANNER`) trả:

```json
{"hits": 0, "misses": 0, "waits": 0, "served": 0,
 "hit_rate": null, "keys": 0, "version": 0, "ttl_seconds": 5.0}
```

| Trường | Nghĩa |
|---|---|
| `hits` / `misses` | dùng lại được / phải chạy truy vấn |
| `hit_rate` | tỉ lệ dùng lại — **con số quyết định §5** |
| `waits` | số lượt phải chờ luồng khác. Cao = chống dồn đang có tác dụng |
| `keys` | số mục đang giữ. Sát 512 = có ai đó sinh key vô hạn |

**Cách đo:** gọi lúc đầu ca, gọi lại cuối ca, lấy hiệu.

Mốc so sánh **đã đo** (§4.12), thay cho ngưỡng tôi đoán lúc đầu:

- `hit_rate` ≈ **0,64** là bình thường ở 22 máy — không phải dấu hiệu xấu
- thấp hơn nhiều → soi xem có ai sinh khoá lạ (`keys` tăng) hay TTL bị đổi
- `waits` ≈ **0** là bình thường lúc chạy đều; nó chỉ nhảy lên khi có cú dồn
  (mọi máy cùng nối lại sau deploy hoặc chớp mạng)

### 4.5 Dọn cache giữa các ca test

Cả hai cache sống theo **tiến trình**, không theo giao dịch — mà fixture `db` rollback
sau mỗi test. Không dọn thì test sau đọc trúng số của test trước, số mà CSDL không còn
giữ nữa. `conftest.py` thêm fixture `autouse` dọn cả hai.

### 4.6 Báo cho trạm kế tiếp — sửa A4

`app/common/vocab/enums.py` thêm `QUEUE_WAITS_ON_PREV_STEP = {2, 4}`: tập trạm có hàng
chờ dựng trực tiếp từ bước của trạm liền trước.

`board/repository.py` dựng `QUEUE_SQL` **từ chính tập đó** thay vì gõ `(2, 4)` — nên
tập hợp là nguồn duy nhất, không trôi khỏi câu SQL được.

`scan/service.py` đánh dấu thêm `station + 1` khi trạm đó nằm trong tập.

**Cách thử:** `tests/test_bao_cho_tram_ke_tiep.py`. Danh sách ca **sinh từ tập hằng**,
không gõ tay — thêm một trạm vào tập mà quên báo cho nó thì test đỏ ngay. Test dựng
lệnh tới đúng trước trạm cần quét, nghe bus, rồi khẳng định ba điều: lệnh có vào hàng
chờ trạm sau, trạm đang quét được báo, và **trạm sau cũng được báo**. Vế thứ ba là vế
đỏ trước khi sửa.

### 4.7 Một lượt quét cho hai màn hình

Bảng đang chạy và Tổng quan đọc **cùng** dữ liệu và **cùng** bị hỏi 10 giây một lần,
nhưng trước đây mỗi màn quét riêng — trả giá hai lần cho một câu trả lời.

`board/service.py` gom lại thành `_running_scan(db)`: một lượt quét `OVERVIEW_SCAN = 200`
dòng, cache dưới khoá `board:running-scan`. `overview` dùng thẳng; `running_board` **cắt
trang ra từ đó** khi `offset + limit <= 200`, xa hơn mới hỏi CSDL.

Cắt được vì cả hai đường đều `ORDER BY code`: n dòng đầu của lượt quét đúng bằng n dòng
đầu SQL trả về.

**Cái bẫy phải tránh:** `running_board` trước đây đổi múi giờ bằng cách **sửa tại chỗ**
từng dict. Dict lấy từ cache dùng chung mà sửa tại chỗ thì lần hỏi sau đổi giờ thêm một
lần nữa — giờ sai mà không ai báo. Nên việc đổi giờ chuyển vào trong hàm dựng cache,
chạy đúng một lần cho mỗi lượt quét.

**Cách thử:** `tests/test_ban_quet_chung.py` — năm nhóm ca: trang cắt ra giống hệt
`LIMIT/OFFSET` của SQL (bốn mốc offset), trang vượt tầm rơi đúng về đường SQL, hai màn
hình chỉ tốn **một** lượt quét, một lượt ghi làm lượt quét chung hết hiệu lực, và giờ
chỉ đổi một lần.

### 4.8 Sửa đường đẩy — A5 + A6

`subscribe_async` bắt event loop **lúc đăng ký** (hàm này chạy trên loop vì endpoint
SSE là `async def`), rồi dùng lại nó ở mọi lần phát. Xoá ba khối mã chết.

`_pending` đổi mặc định sang `None`, `mark_affected` dựng `frozenset` mới thay vì sửa
tại chỗ — không còn vật thể dùng chung để làm bẩn.

**Cách thử:** `tests/test_day_su_kien.py` dùng `asyncio.to_thread` để phát tin từ đúng
loại luồng mà FastAPI dùng cho endpoint ghi. Bốn ca: phát từ threadpool tới được người
nghe, cả đường `mark_affected` + `flush_affected` tới được, giao dịch hỏng giữa chừng
không làm bẩn request sau, và hàng đầy thì bỏ tin chứ không làm hỏng lượt ghi.

### 4.9 Đưa SSE về đúng đường chung — A7

`sse/router.py` trước đây **tự viết lấy phần xác thực**. Ba hậu quả, cả ba đã hết:

| Trước | Sau |
|---|---|
| Mở `SessionLocal()` và tra CSDL ngay trong `async def` → chặn event loop mỗi lần có máy nối vào | `ActorDep` — FastAPI chạy dependency đồng bộ trong threadpool, không đụng loop |
| Không gọi `require_step` → nằm NGOÀI ma trận §12.4; gõ thẳng `/v1/sse/0` là nghe được mọi thay đổi của Kho | `actor.require_step(station, VIEW)`, y hệt `GET /board/queue/{station}` |
| Tự dựng `JSONResponse` 400/401 → khác dạng lỗi với mọi endpoint khác | Ném `Invalid` / để `ActorDep` ném, dùng chung bộ xử lý lỗi |

`ActorDep` đọc cookie trước rồi mới xét header, nên EventSource — vốn không set được
custom header — vẫn dùng được.

Phiên CSDL không bị giữ suốt kết nối: `deps.current_actor` đóng giao dịch chỉ-đọc ngay
sau khi đọc, và khi cache người dùng (§4.3) trúng thì không có truy vấn nào cả.

**Cách thử:** `tests/test_sse_qua_http.py` — bốn ca: tin phát từ luồng khác tới được
`body_iterator` của endpoint (đây là ca A5 trượt suốt, và nó phải đi qua đúng vòng đời
`subscribe_async` của endpoint mới bắt được), chưa đăng nhập → 401, QC gọi
`/v1/sse/0` → 403, trạm không hợp lệ → 422.

Hai ca canh gác kiến trúc đỏ từ đầu tài liệu — `test_MOI_endpoint_deu_khai_bao_quyen`
và `test_router_KHONG_cham_CSDL[sse]` — nay xanh.

### 4.10 Chặn ồn ào khi có người bật nhiều tiến trình — A1 + A2

Không dựng Redis. Chỉ chặn, ở hai lớp:

| Lớp | Làm gì |
|---|---|
| `docker-entrypoint.sh` | thấy `WEB_CONCURRENCY` / `UVICORN_WORKERS` / `GUNICORN_WORKERS` > 1 thì **thoát ngay**, thông báo nằm đầu log triển khai |
| `app/common/single_process.py` | `assert_single_process()` trong `lifespan` — chặn cả khi ai đó gọi uvicorn không qua entrypoint |

Cổng mở: làm xong §5.4 rồi đặt `MES_ALLOW_MULTI_PROCESS=true`.

**Cái này KHÔNG chặn được nhiều BẢN SAO** — mỗi bản sao là một máy chủ riêng, không
đọc được biến môi trường của nhau. Thanh trượt Scaling trên Render vẫn hỏng y hệt, nên
`render.yaml` có ghi chú ngay cạnh chỗ khai biến môi trường.

**Cách thử:** `tests/test_mot_tien_trinh.py` — 12 ca, gồm cả ba biến môi trường (bỏ sót
một cái là bỏ sót cả), giá trị gõ sai (`""`, `"nhieu"`, `"2.5"`) không được biến thành
sự cố khởi động, và thông báo phải nói rõ biến nào gây ra cùng đường mở cổng.

### 4.11 Khoá tư vấn cho migration

`migrations/env.py` ôm `pg_advisory_lock` quanh cả loạt migration. Hai tiến trình cùng
`alembic upgrade head` thì **xếp hàng**: cái thứ hai chờ, vào sau đọc lại
`alembic_version` và thấy không còn gì để làm.

Khoá theo **phiên** chứ không theo giao dịch — `context.run_migrations()` tự commit
giữa chừng, khoá phải giữ qua hết cả loạt.

Hằng số để ở `app/db/migration_lock.py` chứ không ở `env.py`: `env.py` chỉ import được
bên trong một lượt alembic (nó đọc `alembic.context`), nên test không lấy được từ đó,
mà chép con số sang test thì hai bên trôi khỏi nhau không ai báo.

**Cách thử:** `tests/test_khoa_migration.py` — dựng một CSDL rỗng riêng rồi bắn **hai
tiến trình con** `alembic upgrade head` cùng lúc (tiến trình con chứ không phải luồng:
`alembic.context` là proxy cấp module, hai lượt trong một tiến trình sẽ giẫm lên nhau).

Đã kiểm ngược: tạm bỏ khoá ra thì ca này đỏ với

```
DETAIL:  Key (typname, typnamespace)=(alembic_version, 2200) already exists.
```

đúng cảnh giành nhau mà BE-PLAN §10 cảnh báo. Hai ca còn lại canh khoá **thật sự được
ôm** trong lúc migrate (không thì ca đầu có thể xanh vì may) và **được nhả** sau khi xong.

### 4.12 Mô phỏng một ca — đo thật thay vì ước lượng

`tests/test_mo_phong_mot_ca.py`, gắn nhãn `mo_phong` nên **không** nằm trong lượt test
thường:

```
pytest -m mo_phong -s
MES_MP_GIAY=120 pytest -m mo_phong -s     # mỗi chặng 120 giây
```

Dựng CSDL riêng đã migrate, commit thật, rồi cho 22 "máy" hỏi theo đúng nhịp 10/10/30
giây trong khi vài "người quét" sinh lượt ghi thật (phát lệnh → Kho nhận → bàn giao →
Setup nhận). Hai chặng: đầu ca (Kho phát lệnh dồn) và giữa ca.

Chạy ở **tốc độ thật**, không nén thời gian — vì thứ quyết định tỉ lệ dùng lại cache
chính là TTL 5 giây gặp nhịp hỏi 10/30 giây. Nén thời gian là đo mất đúng thứ cần đo.

#### Số đo (60 giây mỗi chặng, 22 máy)

| | Đầu ca | Giữa ca |
|---|---|---|
| Lượt ghi | 54/phút | 4/phút |
| Lượt đọc phục vụ | 68/phút | 68/phút |
| **Cache dùng lại được** | **63,7%** | **65,0%** |
| Truy vấn thật xuống CSDL | 35/phút | 34/phút |
| Truy vấn mỗi lượt đọc | 0,51 | 0,50 |
| Lượt phải chờ máy khác dựng | 0 | 0 |
| Mục cache đang giữ | 4 | 4 |

#### Ba điều số đo nói ra

**1. Nhịp ghi gần như không ảnh hưởng tỉ lệ cache.** 54 so với 4 lượt ghi mỗi phút —
gấp 13 lần — mà chênh 1,3 điểm. §3 đã sửa lại theo số này.

**2. Chống dồn (§4.2) không làm gì lúc chạy đều.** `waits = 0` ở cả hai chặng: 22 máy
lệch pha nhau nên hiếm khi hai máy cùng trượt một khoá đúng lúc. Giá trị của nó nằm ở
**cú dồn** — mọi máy cùng nối lại sau deploy hoặc chớp mạng — chứ không phải ở đây. Giữ
lại vì đúng lúc đó mới là lúc không được sập, nhưng đừng trông nó cải thiện con số
hằng ngày.

**3. Tải thật nhỏ hơn cả ước lượng.** 35 truy vấn/phút ≈ **0,6 truy vấn/giây** xuống
Postgres, ở chặng đông nhất. Câu trả lời cho câu hỏi mở đầu tài liệu — *polling có làm
nghẽn máy chủ không* — là **không**, và giờ có số chứ không phải suy đoán.

Cache vẫn đáng giữ: 0,5 truy vấn mỗi lượt đọc so với ~2 nếu bỏ cache, tức đỡ được ~75%.

### 4.13 Kết quả chạy

- Backend: **365 qua / 0 đỏ / 1 bỏ qua** (366 ca, chưa tính `mo_phong`)
- Mô phỏng: `pytest -m mo_phong -s` — 1 ca, ~2 phút
- `tsc --noEmit`: sạch · `eslint` trên file đã sửa: sạch · `ruff` trên file đã sửa: sạch

Hai ca đỏ tồn tại từ đầu đợt rà soát đã hết sau §4.9. Cả hai đều là canh gác kiến
trúc, và cả hai chỉ đúng vào một chỗ hỏng thật — giữ nguyên chúng thay vì vá tạm là
quyết định đúng.

---

## 5 · Còn lại

### 5.1 ~~`count_running`~~ — đã đo, KHÔNG sửa

Giả thuyết B3 của tôi: `SELECT count(*) FROM (SELECT 1 FROM v_round_board)` phải dựng
cả view, gồm `LATERAL jsonb_agg` trên `v_line_time`. **Đo thì sai.**

`EXPLAIN (ANALYZE, BUFFERS)` trên 12 vòng đang mở:

```
Aggregate
 └─ Hash Join  (m.id = r.mo_id)
     ├─ Seq Scan on manufacturing_order
     └─ Bitmap Index Scan on mo_round_one_open  (closed_at IS NULL)
```

Postgres **cắt sạch**: không `LATERAL`, không `jsonb_agg`, không `v_line_time`, không
`v_round_kpi`, không `production`/`packing`/`warehouse_out`, không cả truy vấn con
`max(step_no)`. Nó giữ đúng hai bảng quyết định số dòng.

| | Thời gian chạy | Buffers |
|---|---|---|
| đếm qua view | 0,095 ms | 3 |
| đếm thẳng `mo_round` | 0,039 ms | 2 |

Chênh lệch là một phép nối băm trên bảng nhỏ. **Không đổi.** Đếm qua view giữ được
điều mà docstring `_count_of` đòi: danh sách và tổng dựng từ **cùng một câu**, không
bao giờ trôi khỏi nhau. Đổi để tiết kiệm 0,05 ms là mua rủi ro bằng tiền lẻ.

Hai cách đếm cho cùng kết quả (12 = 12) tại thời điểm đo, nhưng đó là **trùng khớp
tình cờ** trên tập dữ liệu này, không phải bằng chứng hai câu tương đương.

Việc còn lại trong nhóm này — `overview` quét lại 200 dòng thay vì dùng chung với
`running` — đã làm, xem §4.7.

### 5.2 ~~Vá `mark_affected`~~ — đã rà xong

Kết luận ở §2/A4: chỉ có `scan()` khai thiếu, đã sửa ở §4.6. Mọi hàm khác **đang đúng**,
kể cả những hàm không khai gì.

Cần làm lại lượt rà này khi thêm trạm hoặc đổi `QUEUE_SQL` — câu hỏi cho mỗi hàm ghi
là: *ghi này có làm lệnh XUẤT HIỆN ở hàng chờ của trạm nào không?*

### 5.3 Xoá cache theo phạm vi — chỉ khi §4.4 nói là đáng

`_version` thành `dict[str, int]`. Nguyên tắc **mặc định an toàn**:

- giao dịch **có** gọi `mark_affected` → chỉ xoá phạm vi đó
- giao dịch **không** gọi → xoá sạch, y như bây giờ

Hàm nào không khai phạm vi thì hậu quả chỉ là xoá thừa, **không** phải đưa ra số cũ.
Đó là lý do §2/A4 kết luận "thiếu hẳn thì vô hại, khai không đủ mới nguy hiểm".

`board:counts` và `board:overview` phụ thuộc mọi trạm → cho vào một phạm vi riêng, xoá
khi bất kỳ trạm nào đổi.

### 5.4 Ra chỗ dùng chung — sửa A1 + A2

**Chặn cứng: không xong thì không được bật `-w > 1`.**

| | Postgres `LISTEN/NOTIFY` | Redis Pub/Sub |
|---|---|---|
| Thêm dịch vụ | không | có |
| Phát đúng lúc commit | Postgres tự đảm bảo | phải tự canh |
| Dùng lại cho việc khác | gần như không | rate limit, hàng đợi việc, khoá chung |
| Đủ cho tải xưởng | dư (BE-PLAN §1: vài trăm lượt ghi/ngày) | dư nhiều |

Nguyên tắc chung cho cả hai: **không chuyển nội dung cache vào đó**. Chỉ phát tin
"xoá bảng"; dữ liệu vẫn nằm trong RAM mỗi tiến trình. Chuyển nội dung vào thì mỗi lần
đọc phải qua mạng rồi dựng lại JSON — tự bỏ đi thứ đang gần như miễn phí.

Cả hai giữ nguyên chữ ký `subscribe`/`emit`, nên 18 chỗ gọi `mark_affected` và toàn bộ
service không phải sửa. Đây cũng không phải quyết định một chiều: đổi qua lại chỉ động
vào ruột một file.

Kèm theo, bắt buộc:

- `sse/router.py::_authenticate` đang gọi CSDL **đồng bộ trong `async def`** → chặn cả
  event loop. Nhiều máy cùng nối lại là tắc ở đây. Bọc `run_in_threadpool`, hoặc xác
  thực không chạm CSDL. Sửa xong thì hai ca đỏ ở §4.6 cũng xanh.
- Mất kết nối rồi nối lại được → **xoá sạch cache của tiến trình đó**, vì không biết đã
  bỏ lỡ tin gì.

### 5.5 ~~Tách migration khỏi entrypoint~~ — đã thay bằng cách tốt hơn

Bản trước đề nghị bỏ `alembic upgrade` khỏi `docker-entrypoint.sh` và đưa ra một bước
deploy riêng. **Không làm nữa** — nó bắt đổi quy trình triển khai, và làm sớm thì bản
deploy 1 worker hiện tại ngừng chạy migration ngay.

Thay bằng khoá tư vấn, xem §4.11. Cấm thì bỏ, chuyển sang xếp hàng.

### 5.6 Có nên đổi HẾT polling sang SSE không

Câu trả lời: **không bỏ hết**. Lý do không phải cảm tính — nằm ở phép nhân.

#### Vì sao push rẻ lúc thường mà đắt lúc đông

Push kiểu "báo có đổi rồi tự đi lấy" (`invalidateQueries`) biến **một lượt ghi** thành
**N lượt request**, N là số truy vấn bảng mà tất cả máy đang giữ:

```
18 tablet × 1 (counts)  +  2 bảng tường × 2  +  2 điều độ × 3   ≈  28
```

Đem nhân với nhịp ghi ([BE-PLAN §1](../mes-backend/BE-PLAN.md): vài trăm lượt/ngày,
đỉnh là 100 lệnh trong vài phút đầu ca):

**Số đo thật** (§4.12), thay cho ước lượng ban đầu của tôi:

| | Lượt ghi | Đẩy cho BẢNG | Polling hiện tại |
|---|---|---|---|
| Giữa ca | 4/phút | **88 req/phút** | 68 req/phút |
| Đầu ca | 54/phút | **1188 req/phút** | 68 req/phút |

Kết luận mạnh hơn tôi tưởng: đẩy lời nhắc cho bảng **thua polling ở CẢ HAI chặng**,
không chỉ lúc đông. Với 22 máy cùng nghe, nó chỉ thắng khi nhịp ghi xuống dưới ~3
lượt/phút — mà xưởng đang chạy thì không bao giờ xuống thấp thế.

Riêng đẩy theo TRẠM (đang chạy thật) thì lành: 198 req/phút lúc đầu ca, vì mỗi trạm
chỉ có ~3 tablet nghe chứ không phải cả 22.

Polling có **trần theo thời gian**. Push có trần theo **nhịp ghi** — mà nhịp ghi cao
nhất đúng vào lúc xưởng bận nhất và hệ không được phép chệnh choạng.

Gom sự kiện 1 giây cũng không cứu được: 54 lượt ghi/phút đã dưới 1 lượt/giây, nên gom
1 giây gần như không gộp được gì. Muốn gom cho bằng polling thì phải gom tới ~10 giây,
tức là đã dựng lại polling bằng đường vòng, kèm thêm một đường hỏng im lặng.

#### Cách push thật sự thắng: đẩy DỮ LIỆU, không đẩy lời nhắc

Một lượt ghi → **một** lần dựng dữ liệu ở server (đã có sẵn nhờ lượt quét chung §4.7)
→ phát nguyên văn qua các kết nối SSE đang mở → client `setQueryData`.

Kết quả: **0 request, 0 truy vấn thêm**, bất kể bao nhiêu máy. Làm được vì bốn endpoint
`/board/*` trả **cùng một dữ liệu cho mọi người** — chính `read_cache` đã dựa vào điều
đó.

Giới hạn: `overview` và `counts` (không lọc ngày) hợp hoàn toàn. `running` có phân
trang nên chỉ đẩy gọn được trang đầu; các trang sau vẫn phải đi hỏi.

#### Dù làm cách nào cũng phải giữ một nhịp hỏi chậm

A5 là bằng chứng: đường đẩy **hỏng hoàn toàn** suốt thời gian qua mà không ai biết,
vì nó hỏng kiểu im lặng — kết nối mở, keepalive về đều, chỉ là không có tin.

Những gì `onReconnect` (§4.1) **không** che được: tin bị bỏ vì hàng đầy, tin phát lúc
tiến trình khởi động lại, một chỗ `mark_affected` khai thiếu (§4.6 vừa tìm ra một),
và A1/A2 khi chạy nhiều tiến trình.

Polling 60 giây là thứ duy nhất tự chữa được mọi trường hợp đó. Giá: 1 request/phút/máy
— rẻ hơn nhiều so với một màn hình đứng im mà không ai hay.

#### Tóm lại

| | Nên dùng gì |
|---|---|
| `queue:N`, `at:N` | **Push** — ít máy nghe, người đứng chờ, độ trễ quan trọng |
| `overview`, `counts` | Push **kèm dữ liệu**, hoặc cứ để polling. Đừng push lời nhắc |
| `running` (phân trang) | Polling |
| Mọi thứ | **Giữ một nhịp hỏi chậm làm lưới** |

---

## 6 · Thứ tự

```
✔ 1. SSE nối lại thì nạp lại          A3   đã xong
✔ 2. Bỏ lượt tra người dùng           B1   đã xong
✔ 3. Chống dồn                        B2   đã xong
✔ 4. Bộ đếm                                đã xong — chạy một ca rồi đọc
✔ 5. EXPLAIN count_running            B3   đã đo — KHÔNG sửa, xem §5.1
✔ 6. Rà mark_affected                 A4   đã rà — sửa scan(), xem §4.6

✔ 7. Một lượt quét cho hai màn hình        đã xong, xem §4.7
✔ 8. Sửa đường đẩy                 A5+A6   đã xong, xem §4.8

✔ 9. Sửa sse/router.py                A7   đã xong, xem §4.9 — HẾT test đỏ
✔10. Chặn ồn ào nếu ai bật -w > 1   A1+A2   đã xong, xem §4.10
✔11. Khoá tư vấn cho migration            đã xong, xem §4.11
✔12. Mô phỏng một ca để ĐO              đã xong, xem §4.12

 13. Push kèm DỮ LIỆU cho overview/counts  tuỳ chọn, xem §5.6
 14. Ra chỗ dùng chung             A1+A2   chỉ khi THẬT SỰ cần nhiều bản sao

BỎ    Xoá cache theo phạm vi              chống dồn (§4.2) đã làm thay
```

Việc 14 vẫn để ngỏ **có chủ ý**. Ở tải hiện tại (~1,1 request/giây, dư khoảng 10 lần
trên một tiến trình) chưa cần nhiều bản sao, nên dựng Redis hay `LISTEN/NOTIFY` bây giờ
là giải một bài toán chưa có. Việc 10 và 11 che rủi ro đó bằng ~15 dòng thay vì một
dịch vụ mới — và việc 10 sẽ là thứ báo cho bạn biết khi nào thật sự tới lúc làm việc 14.

---

## 7 · Chỗ dễ hiểu nhầm

**"Bỏ polling đi cho nhẹ máy chủ."** Polling không phải thứ làm nặng. Bỏ hết polling
mà chưa sửa A1/A2 thì đổi một vấn đề hiệu năng không có thật lấy hai lỗi sai kết quả
có thật. A3 và A4 là ví dụ sống: cả hai đều là lỗi của đường ĐẨY, và cả hai chỉ nguy
hiểm vì `queue`/`at` đã bỏ polling — còn polling thì màn hình tự đúng lại sau 10 giây.

**"Đo làm gì, nhìn code là biết."** §5.1 là phản ví dụ: kế hoạch truy vấn thật khác
hẳn thứ đọc câu SQL mà suy ra, và nếu "sửa cho chắc" thì đã đánh đổi một bất biến
(danh sách và tổng dựng từ cùng một câu) lấy 0,05 ms.

**"Có Redis rồi thì chuyển cache vào Redis luôn."** Không. Xem §5.4.

**"Cache đang chạy tốt, docstring nói 0,6 truy vấn/giây."** Con số đó đúng khi xưởng
đứng im. Đọc `hit_rate` thật ở §4.4 trước khi tin.

**"Máy chủ mạnh hơn là hết."** Hết B1–B3. A1 và A2 thì **nặng thêm**, vì máy chủ mạnh
là lý do để bật nhiều tiến trình.
