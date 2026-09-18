# Kế hoạch — Báo cáo sản xuất

Thêm mục `Báo cáo sản xuất` vào nhóm **Xem chung** ở sidebar.

Bản demo: [`mockup/bao-cao-san-xuat.html`](mockup/bao-cao-san-xuat.html)
Cơ sở chọn dạng biểu đồ: [`NGHIEN-CUU-BIEU-DO-SAN-LUONG-GIO.md`](NGHIEN-CUU-BIEU-DO-SAN-LUONG-GIO.md)

> **File này mô tả đúng cái mockup đang có**, không mô tả ý định. Chỗ nào mockup chưa
> dựng thì ghi rõ là **chưa dựng** — để không ai đọc kế hoạch xong tưởng đã có sẵn.

---

## 1 · Phân tích vấn đề

### 1.1 Dữ liệu đã có tới đâu

| Biểu đồ | Nguồn | Còn thiếu |
|---|---|---|
| ① Tiến độ theo lệnh | `v_mo_progress` — có `quantity`, `qty_done`, `qty_remain`, `qty_ng_total`, `qty_short_total` | một endpoint |
| ② Đạt định mức theo giờ | `hourly_output` — có `work_date`, `slot_hour`, `target_qty`, `qty`, `headcount`, `note` | một endpoint |
| ③ Lệnh ở từng bước | `GET /board/counts` — **đã trả đủ** `counts` và `holding` | **không thiếu gì** |

Biểu đồ ③ gần như miễn phí. ② tốn công nhất.

**`hourly_output` đã CHÍNH LÀ một bảng theo giờ chuẩn lean.** Lean Enterprise Institute
gọi nó là *Production Analysis Board*, và bốn thứ nó mô tả — khung giờ, định mức, thực
tế, lý do — đúng bằng `slot_hour · target_qty · qty · note`. Không phải đổi lược đồ để
khớp chuẩn.

### 1.2 Bốn cái bẫy phải xử trước khi viết code

**Bẫy A — không được lấy trung bình của phần trăm.**

`Đạt %` là tỷ lệ (`thực tế ÷ yêu cầu`). Gộp bốn giờ thành một điểm mà lấy trung bình
bốn phần trăm là sai:

```
Giờ 1:  định mức 1.000, làm được   500  =   50%
Giờ 2:  định mức   100, làm được   100  =  100%
                             trung bình  =   75%    ← SAI
                        600 / 1.100      =  54,5%   ← ĐÚNG
```

Phải cộng tử rồi cộng mẫu: `Σqty ÷ Σtarget_qty`. Cùng một bẫy khi gộp **theo lệnh**:
lấy trung bình 100 con phần trăm thì lệnh chạy 20 cái nặng ngang lệnh chạy 20.000.

Mockup cài đúng chỗ này ở hai nơi: `bucketize()` cộng `qty`/`target` rồi mới chia, và
`ranking()` cũng vậy khi gộp nhiều giờ của một lệnh.

**Bẫy B — `target_qty` có thể NULL.** Cột này thêm ở migration `0006`. Coi NULL là 0 thì
phép chia nổ. Loại hẳn dòng thiếu khỏi **cả tử lẫn mẫu**, và **đếm ra trên màn hình**
(`Đã bỏ n dòng chưa khai sản lượng yêu cầu…`).

**Bẫy C — khung giờ không ghi sổ không được nối liền.** Bỏ sót vài khung là chuyện
thường. Dạng đường nối thẳng qua đó — đo trên dữ liệu demo ở khung 1 giờ, nó bịa ra
**7 mốc không có thật**. Mockup tránh hẳn: ô chọn giờ **chỉ liệt kê khung có ghi sổ**,
khung trống thì không có mục, không có ô rỗng, không có đường nối.

**Bẫy D — bốn token màu của app KHÔNG dùng làm màu chuỗi được.**

```
#0E6E99 accent · #0A7A34 ok · #8A5A06 warn · #B02A2A danger

[FAIL] CVD separation      #B02A2A ↔ #8A5A06  ΔE 1,6 (deutan)
[FAIL] Normal-vision floor #B02A2A ↔ #8A5A06  ΔE 12,5 — dưới ngưỡng 15
       và                  #B02A2A ↔ #0A7A34  ΔE 2,4 (deutan)
```

Người mù màu đỏ–lục không phân biệt nổi `danger` với `warn`, cũng không phân biệt nổi
`danger` với `ok`. Thêm lý do độc lập: màu trạng thái là **màu dành riêng** — `danger`
đỏ đang mang nghĩa *hỏng/dừng* trong app.

Cách xử: hai bảng màu riêng, đều đã đo bằng máy — xem §3.3.

### 1.3 Ai xem được báo cáo — ĐÃ CHỐT: MỌI VAI

§9b.5 cho `Bảng đang chạy` là ngoại lệ (cả xưởng xem được); §12.4 lại giới hạn theo
trạm. Báo cáo tổng nằm giữa, và **chốt theo §9b.5**: mọi vai đều xem được.

Lý do đứng vững: ở đây chỉ có số cộng dồn của cả xưởng — **không có hàng đợi, không
có danh sách lệnh đang nằm trong tay trạm nào**, tức không có thứ mà §12.4 sinh ra để che.

Hai endpoint vì thế khai trong `CO_Y_MO` của `tests/test_permissions.py`, cùng khuôn
với `/board/running` và `/board/counts`.

**Nếu sau này muốn siết lại** thành `PLANNER` + `*_LEADER`: sửa đúng hai chỗ — thêm
`require_any_role(…)` vào hai hàm trong `reports/router.py`, và bỏ hai đường dẫn khỏi
`CO_Y_MO`. `actor.require_role()` hiện chỉ nhận ĐÚNG MỘT vai nên phải viết thêm hàm
nhận nhiều vai. Đường lùi này ghi sẵn trong docstring của `reports/router.py`.

---

## 2 · Giải thích đúng yêu cầu

**① Tiến độ theo lệnh** — mỗi lệnh một dòng. Đo bằng **pcs đã nhập kho** (`qty_done`),
không phải SL đạt: hàng đạt mà chưa đóng thùng thì chưa tính (§6b.2).

**② Đạt định mức theo giờ** — `sản lượng thực tế ÷ sản lượng yêu cầu`, mục tiêu **85%**.
Không phải `pcs/người`; `headcount` vẫn ghi sổ theo §7.2b nhưng **không còn là mẫu số**,
nó về bảng số để đối chiếu.

**③ Lệnh ở từng bước** — sáu trạm, tách **chờ nhận** và **đang làm**. Gộp lại thì không
phân biệt được *việc cần người đi quét* với *việc đang chạy*.

### Ba người xem hỏi ba câu khác nhau

| Người xem | Câu hỏi | Dạng | Mockup |
|---|---|---|---|
| **Tổ trưởng** | giờ này lệnh nào hụt | chọn ngày + khung giờ → thanh xếp hạng mọi lệnh | **ĐÃ DỰNG** |
| **Thợ ở trạm** | giờ vừa rồi có đạt không, hụt vì đâu | bảng theo giờ có cột Lý do + bullet cộng dồn ca | chưa dựng |
| **Điều độ** | cả xưởng đang lên hay tụt | số dẫn → cột thời gian một chuỗi → xếp hạng | chưa dựng |

**Mockup hiện chỉ dựng màn Tổ trưởng.** Hai màn kia mới là phân tích, chưa phải thiết
kế — đừng đọc bảng trên rồi tưởng có sẵn ba màn.

Màn Thợ ở trạm vẫn đáng làm, và lý do vẫn đứng vững: LEI mô tả bảng theo giờ là *công cụ
giải quyết vấn đề* — *"khi sản lượng không khớp kế hoạch thì ghi lại vấn đề và tìm nguyên
nhân"* — nên **cột quan trọng nhất là cột chữ**. `hourly_output.note` đã có sẵn cột đó,
và màn Tổ trưởng hiện **chưa dùng tới nó**.

---

## 3 · Phương án triển khai

### 3.1 Chọn dạng — và vì sao

| # | Việc người đọc phải làm | Dạng trong mockup | Vai trò màu |
|---|---|---|---|
| ① | so tiến độ giữa các lệnh | thanh ngang có rãnh nền | một sắc + xám nền |
| ② | tìm lệnh hụt trong một khung giờ | thanh ngang xếp hạng, tệ nhất lên đầu | **ba bậc** đỏ/lam/lục |
| ③ | so số lượng giữa sáu bước | **cột đứng gom nhóm**, giữ thứ tự 0→5 | phân loại (2 ô) |

**Số dẫn ở đầu biểu đồ ②.** Một con số cỡ 42px — `Σthực tế ÷ Σđịnh mức` của đúng khung
đang chọn — rồi mới tới dãy thanh. Người xem biết ngay "khung này ổn hay không" trước
khi phải đọc từng dòng. Số này in **đỏ** khi dưới mục tiêu.

**① dùng thanh có rãnh nền chứ không phải biểu đồ tròn.** Một tỷ lệ so với hạn mức thì
thanh đọc nhanh hơn, và xếp nhiều dòng thì so được giữa các lệnh.

**③ KHÔNG sắp theo giá trị.** Thứ tự 0→5 là thứ tự quy trình; sắp theo số thì mất luôn
thông tin *hàng đang dồn ở khúc nào*.

**Riêng ③ dùng cột ĐỨNG, hai biểu đồ kia nằm NGANG.** Không phải tuỳ hứng: cột đứng
chỉ đọc được khi nhãn kê vừa dưới chân cột mà không phải xoay chữ. Sáu trạm với tên
hai ba chữ thì vừa; hai mươi mã lệnh bảy ký tự (①) hay một trăm lệnh trong một khung
giờ (②) thì không — chỗ đó vẫn phải nằm ngang.

**Hai cột đứng SÁT CẠNH NHAU, không xếp chồng.** `Chờ nhận` và `Đang làm` là hai câu
hỏi khác nhau, không phải hai phần của một tổng. Xếp chồng thì phải ước lượng độ dài
từng đoạn mới so được trạm này với trạm kia; để cạnh nhau thì cả hai cùng đứng trên một
vạch chân.

Gom nhóm chỉ chịu được **ít chuỗi**: UK Government Analysis Function đặt trần 4 cột mỗi
cụm, ở đây 2 chuỗi × 6 trạm = 12 cột, còn rộng chán. Đem đúng dạng này cho ② thì vỡ ngay
— 100 lệnh trong một khung giờ là 100 cột một cụm (§3.2).

**Mẫu số là CỘT CAO NHẤT, không phải tổng nhóm.** Lấy tổng thì mọi cột lùn đi một nửa
và chênh lệch giữa các trạm khó thấy hơn.

**Cột bằng 0 vẫn phải THẤY được** — vẽ một vạch chân 2px thay vì bỏ trống, không thì
không phân biệt nổi *trạm này rỗng* với *trạm này chưa có số liệu*.

### 3.2 Vì sao KHÔNG dùng cột nhóm

Bản thiết kế đầu gộp hai chiều (thời gian × lệnh) vào một hình. Số đo:

```
Gộp chung — 1 mốc = N cột
    3 lệnh →    48 cột | mỗi cột 10,0px
    8 lệnh →   128 cột | mỗi cột  2,5px   ← không vẽ nổi
  100 lệnh →  1600 cột | mỗi cột −1,6px
```

Chặn cứng hơn cả: **bảng màu phân loại đã kiểm chỉ có 3 ô** đạt chuẩn, tối đa 8. Màu
thứ 9 nhìn giống màu đã có dưới mắt người mù màu.

Ngưỡng này có chuẩn: UK Government Analysis Function quy định **tối đa 4 cột mỗi cụm**;
IBCS coi **quá 3 đường là spaghetti chart**.

Cách chữa: **biến thời gian thành BỘ LỌC**, trục chỉ còn một chiều. Chọn ngày và khung
giờ → hiện mọi lệnh chạy trong khung đó, xếp tệ nhất lên đầu. Chịu được 100 lệnh mà
không thêm màu nào. Dùng ô **Số lệnh đang chạy** (3 · 8 · 24 · 100) trong mockup để tự
kiểm chỗ này.

**Bù lại chiều thời gian đã lấy đi:** mỗi dòng mang **mũi tên chênh so với khung trước**
(`▼22,7`) — hụt lần đầu khác hẳn hụt lần thứ tư liên tiếp. Khung trước lấy theo **toàn
kỳ chứ không theo ngày**: khung đầu ngày phải so được với khung cuối ngày hôm trước,
nếu không thì mỗi sáng mũi tên trống trơn.

**Trần cắt dòng KHÔNG được giấu lệnh hụt.** Với 100 lệnh, một khung có 89 lệnh chạy và
37 hụt; trần cứng 25 sẽ cắt mất 12 lệnh cần xử lý — đúng thứ màn này sinh ra để chỉ.
Trần là `max(25, số hụt)`, và phần cắt bỏ nói rõ ra:
`Còn n lệnh nữa, tất cả đều đạt mục tiêu.`

### 3.3 Màu — đã kiểm bằng máy

Hai bảng màu cho hai việc khác nhau. **Không trộn.**

#### a) Bảng phân loại — biểu đồ ③ (`chờ nhận` / `đang làm`)

| Ô | Sắc | Sáng | Tối |
|---|---|---|---|
| 1 | lam | `#2a78d6` | `#3987e5` |
| 2 | cam | `#eb6834` | `#d95926` |
| 3 | lục lam | `#1baf7a` | `#199e70` |

```
Sáng: [PASS] CVD ΔE 24,7 (protan) · [PASS] mắt thường ΔE 33,6 · [PASS] tương phản ≥ 3:1
Tối : [PASS] CVD ΔE 26,8 (protan) · [PASS] mắt thường ΔE 31,8 · [PASS] tương phản ≥ 3:1
```

Số đo trên là của **hai ô đang thực dùng**. Ô thứ ba khai sẵn nhưng chưa dùng tới — để
đó cho lúc biểu đồ ③ cần tách thêm một trạng thái.

#### b) Bảng ba bậc — thanh xếp hạng của biểu đồ ②

Thanh xếp hạng chỉ có **một đại lượng**, nên màu ở đây nói **bậc**, không nói danh tính:

| Bậc | Ý nghĩa | Sáng | Tối |
|---|---|---|---|
| `< 85%` | hụt | đỏ `#A32222` | `#c83737` |
| `85–100%` | đạt mục tiêu | lam `#2a78d6` | `#2d82d7` |
| `> 100%` | vượt định mức | lục `#34A653` | `#40ad6a` |

```
Sáng: [PASS] CVD ΔE 16,2 (deutan) · [PASS] mắt thường ΔE 26,6 · [PASS] tương phản ≥ 3:1
Tối : [PASS] CVD ΔE 10,5 (deutan) · [PASS] mắt thường ΔE 23,3 · [PASS] tương phản ≥ 3:1
```

**Không dùng thẳng token trạng thái của app** — lý do ở Bẫy D. Phải kéo lục sáng lên và
đỏ đậm xuống mới đủ tách, vì dưới deuteranopia thì **độ sáng là thứ duy nhất còn phân
biệt được** đỏ với lục.

**Màu không được là kênh duy nhất.** Mỗi thanh mang thêm **hai vạch dọc** đúng chỗ `85%`
và `100%` — tức đúng hai ranh giới màu — nên bậc đọc được bằng **vị trí** cả khi in đen
trắng. Kèm chú giải ba ô phía trên và con số `%` ở cuối mỗi dòng. Thang ngang luôn ôm
trọn mốc `100%` (`top = max(rate…, 100) × 1,06`); thiếu một vạch thì mất luôn cách đọc
bằng vị trí.

Ranh giới đã kiểm: `84,99 → đỏ` · `85 → lam` · `100 → lam` · `100,01 → lục`.

Khai thành token trong `globals.css` cho cả hai chế độ (`--color-series-1..3` và
`--color-tier-low/mid/high`), không rải hằng số màu trong component.

**Nút `Xem dạng bảng` ở cả ba biểu đồ là bắt buộc**, không phải tiện ích — người xem cần
đọc con số chính xác và cần copy được. Hai bảng màu trên không còn cảnh báo tương phản
nào, nhưng bảng số vẫn là đường lui duy nhất khi màn hình xưởng bị chói hoặc khi in ra giấy.

### 3.4 Thư viện — không cài thêm, và không cần cả SVG

Dự án hiện **không có thư viện biểu đồ nào**, và mockup chứng minh là không cần:
mọi biểu đồ ở đây vẽ bằng **`div` + CSS thuần**, không một thẻ SVG nào. Thanh là `div`
đặt `width: n%`; thanh xếp chồng là flexbox; vạch mốc là `position: absolute`.

Ba lý do:

1. **Theming.** App đổi sáng/tối bằng biến CSS. Recharts nhận màu là chuỗi JS — phải đọc
   biến CSS lúc chạy rồi vẽ lại. HTML thuần dùng thẳng `var(--color-tier-low)`.
2. **Dung lượng.** Recharts ≈ 100KB nén; máy tính bảng đi wifi nhà máy.
3. **Khối lượng nhỏ.** Demo đã chứng minh: cả ba biểu đồ gọn trong một file, không có
   trục toạ độ nào phải vẽ.

Cái giá: dạng nào cần trục thật (đường, tán xạ) thì HTML thuần đuối. Ba biểu đồ hiện tại
không có cái nào như vậy. Nếu sau này màn **Điều độ** cần cột theo thời gian có trục thì
tính lại lúc đó — đừng cài trước.

### 3.5 Backend — hai endpoint mới

```
GET /v1/reports/mo-progress?status=PROCESSING&limit=20
    → [{ code, product_name, quantity, qty_done, qty_remain, qty_ng_total, qty_short_total }]

GET /v1/reports/hourly?bucket=1&from=…&to=…&codes=…
    → { bucket, target_pct: 85,
        shift: { day_start: 6, shift_start: 8, lunch_start: 12,
                 lunch_end: 13, shift_end: 17, day_end: 22 },
        series: [{ code, points: [{ at, qty, target_qty, headcount, note }] }],
        skipped_rows, folded_rows }
```

Một endpoint phục vụ **cả ba màn** — chỉ khác cách FE trình bày. Trả **số thô**, phần trăm
tính ở FE: trả tỷ lệ tính sẵn thì FE không cộng lại được khi đổi cách gộp, và sinh ra
hai công thức ở hai nơi.

`target_pct` trả từ server chứ không hằng số ở FE — ngưỡng là **thoả thuận nghiệp vụ**.

`skipped_rows` là Bẫy B (thiếu định mức, bỏ hẳn). `folded_rows` là số dòng bị đẩy sang
khung khác với giờ thật của nó. Hai con số khác nhau, cả hai đều phải hiện ra màn hình.

#### Khung gộp

Khung bám **giờ đi làm**, không chia đều từ nửa đêm:

```
ngày làm việc  08:00–17:00      nghỉ trưa  12:00–13:00

1 giờ   →  cả ngày   06–07 07–08 … 20–21 21–22      (16 khung)
4 giờ   →  2 khung   08:00–12:00 │ 13:00–17:00
9 giờ   →  1 khung   08:00–17:00   (cả ca)
```

**Khung 1 giờ trải cả ngày, khung gom thì bám giờ đi làm.** Mỗi giờ một ô thì không ô
nào đụng đến ô nào — giờ tăng ca hiện nguyên hình, giờ nghỉ trưa không có sổ thì không
có ô (Bẫy C).

Gom lại thì ngược: một khung ôm giờ nghỉ trưa sẽ **tụt oan**, và người xem mất công đi
tìm lý do cho một việc không có thật. Nên khung gom cắt theo **buổi**.

**Vì sao khung gom không chia đều:**

| Cách chia | Kết quả |
|---|---|
| đều từ nửa đêm | `04–08` và `20–00` rỗng trơn; khung `12–16` dính giờ nghỉ trưa |
| đều từ đầu ca | `08–12` đúng, nhưng `12–16` vẫn dính trưa và `16–20` chỉ còn 1 giờ |
| **theo khối làm việc** | `08–12` và `13–17` — đúng hai buổi, giống nhau mọi ngày |

`9 giờ` là **khoảng cách đầu–cuối ca** (08→17), trong đó 8 giờ làm và 1 giờ nghỉ.

Vì khung không đều nhau nên **`date_bin` không dùng được** — nó chỉ biết chia đều.
Thay bằng `CASE` theo khối:

```sql
h.work_date + make_interval(hours =>
  CASE
    WHEN :bucket  = 1    THEN h.slot_hour
    WHEN :bucket >= 9    THEN 8
    WHEN h.slot_hour < 13
      THEN 8  + ((least(greatest(h.slot_hour,  8), 11) -  8) / :bucket) * :bucket
    ELSE 13 + ((least(greatest(h.slot_hour, 13), 16) - 13) / :bucket) * :bucket
  END) AS at
```

Đã đối chiếu biểu thức này với JS của mockup trên cả `06:00–22:00` × ba khung — khớp
từng giờ một.

Nhánh `:bucket = 1` không kẹp gì cả — giờ nào ở yên giờ đó.

`least/greatest` ở hai nhánh còn lại là phần **ghép giờ ngoài ca vào khung gần nhất**,
không phải thừa: tăng ca 17–19h và trưa không nghỉ là chuyện có thật. Bỏ hẳn những dòng
đó thì **tổng trên màn hình khác tổng trong sổ** — lỗi nặng hơn nhiều so với nhãn khung
hơi rộng. Đếm số dòng đó, **nói ra dưới biểu đồ**, kèm câu chỉ đường: xem khung **1 giờ**
để thấy đúng giờ thật của chúng.

Sáu mốc `6 · 8 · 12 · 13 · 17 · 22` để **một chỗ** — hằng số cấu hình backend, trả kèm
trong response (`shift`) để FE vẽ nhãn theo, không chép tay sang JS. Đổi giờ làm thì sửa
một nơi.

Gom ở **SQL chứ không ở JS**: một lệnh chạy một tuần đã ~168 dòng, nhiều lệnh thì
payload phình theo tích số.

Phân quyền: mở cho mọi vai theo §1.3.

### 3.6 Những chi tiết nhỏ trong mockup phải giữ khi làm thật

Dễ rơi mất lúc chuyển sang React, nên liệt ra:

| Chi tiết | Vì sao có |
|---|---|
| **Hai ô chọn**: `<input type="date">` + dropdown giờ | một ô gộp cả ngày lẫn giờ thì xem 30 ngày là 480 mục, không ai cuộn nổi. Tách ra còn `30 + 16`. Ô ngày có `min`/`max` đúng khoảng có dữ liệu |
| **Dòng tóm tắt ngày** ngay dưới thanh chọn | ô nhập ngày của trình duyệt không gắn nhãn được, nên phần *"ngày này có mấy khung, mấy khung có lệnh hụt"* phải nằm riêng một dòng |
| Dropdown giờ **không kèm số lệnh** | số lệnh và số hụt của khung đang chọn đã nằm ngay dòng số dẫn bên dưới — nhắc lại trong ô chọn là đọc hai lần một thứ |
| Dropdown **chỉ liệt kê khung có ghi sổ** | Bẫy C |
| `meta` ở tiêu đề thẻ ② ghi **cả kỳ** `n/N lệnh dưới mục tiêu` | khung đang xem là một lát cắt; con số cả kỳ giữ bối cảnh |
| Đổi khung / đổi ngày thì **xoá ô giờ rồi vẽ lại** | mốc giờ của khung cũ không còn tồn tại ở khung mới |
| `title` trên mọi thanh và mọi vạch mốc | thay cho tooltip, không cần thêm JS |

Ô **Số lệnh đang chạy** (3/8/24/100) chỉ là **giả lập của mockup** để soi chỗ gãy —
**không đưa vào bản thật**.

---

## 4 · Đề xuất ưu tiên

| | Việc | Vì sao thứ tự này | Công |
|---|---|---|---|
| ~~P0~~ | Trang + mục sidebar + **biểu đồ ③** | **XONG** | — |
| ~~P1~~ | **② màn Tổ trưởng** — chọn ngày/khung + xếp hạng ba bậc | **XONG** | — |
| ~~P2~~ | **①** tiến độ theo lệnh | **XONG** | — |
| **P3** | Xuất CSV cho cả ba | `Xem dạng bảng` đã có sẵn trong `ChartFrame`; còn nút tải về | ~1h |
| **P4** | **② màn Thợ ở trạm** — bảng theo giờ có cột Lý do + bullet | chuẩn lean, nhưng **chưa có mockup** — phải thiết kế trước | ~5h |
| **P5** | **② màn Điều độ** — số dẫn + cột thời gian | ít người dùng nhất, nặng nhất, cũng **chưa có mockup** | ~4h |

Đổi so với bản trước: **màn Tổ trưởng lên P1** thay cho màn Trạm. Lý do thẳng thắn — đó
là màn đã vẽ xong và đã kiểm; hai màn kia mới chỉ có lập luận.

---

## 5 · Các file cần thay đổi

### Backend — ĐÃ DỰNG XONG

> `249 passed, 1 skipped` · `ruff` sạch · migration `0010` đã chạy.

| File | Trạng thái |
|---|---|
| `app/modules/reports/{__init__,shift,schemas,repository,service,router}.py` | mới |
| `app/router.py` | đã gắn, docstring đổi `10` → `11` tính năng |
| `app/common/config.py` | thêm nhóm `ReportSettings` (lớp + trường `Settings` + dòng `GROUPS`) |
| `.env.example` | thêm khối `MES_REPORT_*` |
| `tests/test_permissions.py` | khai hai đường dẫn vào `CO_Y_MO` kèm lý do |
| `tests/test_reports.py` | mới — 18 test |
| `app/db/migrations/versions/0010_chi_muc_bao_cao.py` | mới |

Phân quyền đã chốt ở §1.3: **mở cho mọi vai**, cùng khuôn với `/board/running`.

---

Phần dưới đây là lý do đằng sau từng dòng — **đã đối chiếu với mã nguồn**, không ước lượng.

| File | Việc |
|---|---|
| `app/modules/reports/{__init__,repository,service,router,schemas}.py` | mới — module riêng, không nhét vào `board` |
| `app/router.py` | gắn router mới; docstring đang ghi *"10 tính năng"* → **11** |
| `app/common/config.py` | nhóm `ReportSettings` — sửa **ba chỗ**: lớp mới, trường trong `Settings`, một dòng trong `GROUPS` |
| `.env.example` | thêm `MES_REPORT_*` — không khai ở đây thì không ai biết biến tồn tại |
| `app/common/security/permissions.py` · `actor.py` | **bắt buộc động** — xem dưới |
| `tests/test_permissions.py` | **sẽ đỏ ngay** khi thêm route — xem dưới |
| `tests/test_reports.py` | mới — Bẫy A, Bẫy B, và bảng khung giờ ở §3.5 |
| `app/db/migrations/versions/00xx_chi_muc_san_luong_gio.py` | chỉ mục mới — xem dưới |

#### Phân quyền: mô hình hiện tại KHÔNG có chỗ cho báo cáo

Mọi luật quyền hôm nay đều đi qua `permission_for(roles, step_no)` — **gắn với trạm**.
Báo cáo tổng không thuộc trạm nào, nên không có đường nào diễn đạt nó bằng bảng hiện có.
Hai lối ra, cả hai đều phải sửa file:

- **Mở cho mọi vai** (đề xuất ở §1.3, cùng tinh thần §9b.5 như `/board/running`) → không
  thêm luật, nhưng **phải khai hai đường dẫn vào `CO_Y_MO`** trong `tests/test_permissions.py`
  kèm lý do viết ra chữ.
- **Giới hạn `PLANNER` + `*_LEADER`** → `actor.require_role()` hiện **chỉ nhận đúng một
  vai** (docstring ghi rõ *"chỉ dùng cho PLANNER"*). Cần thêm `require_any_role()` hoặc
  một hàm `can_view_reports(roles)` trong `permissions.py`.

Chốt §1.3 xong mới biết đi lối nào — nhưng **không có lối nào là không đụng file**.

#### `tests/test_permissions.py` sẽ đỏ, không phải "có thể đỏ"

Test cuối file duyệt **toàn bộ** `app.routes` và đòi mã nguồn của mỗi endpoint phải chứa
`require_step(` / `require_role(` / `require_station(`, trừ khi đường dẫn nằm trong danh
sách `CO_Y_MO` **có ghi lý do**. Thêm hai endpoint báo cáo mà không xử là test đỏ ngay.

Đây là thiết kế đúng, không phải phiền toái: nó chặn đúng cái lỗi *"quên gắn quyền"*.

#### `tests/test_kien_truc.py` không phải sửa, nhưng nó **ràng buộc thiết kế**

Test này tự quét `modules/*/service.py` và `modules/*/router.py`, nên module mới vào
khuôn ngay từ dòng đầu:

- **Mọi `text(` phải nằm trong `repository.py`** — kể cả biểu thức `CASE` gộp khung giờ
  ở §3.5. Service không được dựng truy vấn.
- **Router KHÔNG được gọi thẳng `_repo.`** Ngoại lệ đọc-thẳng hiện chỉ mở cho `catalog/`
  và `mo/`, và nó **ghi cứng theo tên module** trong test. `reports/` phải đi đủ
  router → service → repository, dù chỉ là đọc.

#### MỘT câu SQL, không N+1

Cả báo cáo sản lượng giờ là **một lượt đi về**, bất kể bao nhiêu lệnh đang chạy:

```
WITH bounded AS MATERIALIZED ( … quét hourly_output ĐÚNG MỘT LẦN … ),
     tally   AS ( đếm dòng thiếu định mức + dòng ngoài giờ, đọc lại bounded ),
     grouped AS ( gộp theo (mã lệnh, khung giờ),      đọc lại bounded )
SELECT … FROM tally t LEFT JOIN grouped g ON true
```

Ba chỗ hay sinh N+1, chặn cả ba:

| Cách viết tự nhiên | Hậu quả | Đã làm thay |
|---|---|---|
| lấy danh sách lệnh rồi hỏi sản lượng từng lệnh | 100 lệnh → 101 câu | gộp `GROUP BY code, at` trong một câu |
| tra `round_id` → `code` sau khi đã lấy số | thêm một lượt mỗi vòng | `manufacturing_order` nối sẵn trong câu |
| đếm `skipped`/`folded` bằng câu riêng | thêm hai lượt quét bảng | `tally` đọc lại CTE đã vật chất hoá |

`MATERIALIZED` là cốt lõi: bỏ nó thì Postgres nội tuyến CTE và quét `hourly_output`
**ba lần** cho cùng một khoảng ngày. Đã đọc `EXPLAIN` để xác nhận: `CTE bounded` xuất
hiện một lần, hai nhánh còn lại đều là `CTE Scan on bounded`.

**`tally LEFT JOIN grouped` chứ không lọc thẳng.** Dòng thiếu định mức bị loại khỏi phần
gộp, nên khoảng ngày toàn dòng thiếu sẽ cho phần gộp **rỗng** — và con số *"đã bỏ n
dòng"* biến mất đúng lúc nó cần nhất. `tally` luôn có đúng một dòng nên bộ đếm không mất.
Có test riêng cho đúng tình huống này.

**Biểu thức gộp khung SINH RA từ `shift.bins_of()`**, không viết tay `CASE` song song:

```
khung 4h  bins=[(8,12), (13,17)]   →   CASE WHEN slot_hour >= 13 THEN 13 ELSE 8 END
khung 9h  bins=[(8,17)]            →   8
```

Xét theo giờ **bắt đầu giảm dần** chứ không theo giờ kết thúc: 12:00 ở khung 4 giờ phải
về buổi sáng, xét theo giờ kết thúc thì nó nhảy sang buổi chiều. Có test cho **cả 24
giờ × ba khung** đi qua cả đường SQL lẫn đường Python rồi so — "sinh ra từ" không đảm
bảo "chạy giống".

#### Cache đọc — không phải tuỳ chọn

Báo cáo trả **cùng một dữ liệu cho mọi người**, đúng hoàn cảnh `read_cache` sinh ra:
50 máy tính bảng cùng mở thì không có lý do gì chạy 50 lượt gộp. Dùng
`read_cache.cached(f"reports:hourly:{bucket}:{from}:{to}:{codes}", …)`.

Kèm một cái bẫy: khoá cache lấy từ **tham số của client**, mà `_store` là dict không
giới hạn. Không chặn miền giá trị thì gọi 10.000 lần với 10.000 khoảng ngày khác nhau
là 10.000 mục cache nằm lại trong RAM.

#### Không tin gì từ client

| Tham số | Chặn |
|---|---|
| `bucket` | `Literal[1, 4, 9]` — sai giá trị thì FastAPI trả 422, không cần mã lỗi mới |
| `from` / `to` | bắt `from <= to`, và **chặn trần độ dài khoảng** (đề xuất 31 ngày) |
| `codes` | chặn số lượng phần tử; mỗi phần tử theo `MoCode` đã có ở `common/schemas.py` |
| `limit` | kẹp `max(1, min(limit, 100))` — y như `GET /mos/{code}/events` đang làm |

Thiếu trần khoảng ngày thì `from=1900-01-01` quét sạch bảng, và cache giữ nguyên kết quả
đó 5 giây cho mọi người cùng chịu.

#### Migration: **có cần**, khác với bản kế hoạch trước

Chỉ mục duy nhất trên `hourly_output` hiện là:

```sql
CREATE INDEX ON hourly_output (round_id, work_date, slot_hour);   -- 0001_init
```

Cột dẫn đầu là `round_id`. Báo cáo lọc theo **khoảng ngày trên mọi vòng**
(`WHERE work_date BETWEEN …`) nên **không dùng được chỉ mục này** — Postgres quét toàn
bảng. Ước lượng: 100 lệnh × 16 giờ = 1.600 dòng/ngày, khoảng **500 nghìn dòng/năm**, quét
lại từ đầu mỗi lần ai đó mở trang.

Cần thêm `CREATE INDEX ON hourly_output (work_date, slot_hour)`. Việc nhỏ, nhưng nó có
nghĩa là **câu "không cần migration cho MVP" ở bản trước là sai**.

### Frontend — ĐÃ DỰNG XONG (P0 · P1 · P2)

> `tsc` sạch · `eslint` sạch · `next build` qua · ba đường dẫn trả 200 trên máy thật.

| File | Trạng thái |
|---|---|
| `src/app/globals.css` · `tailwind.config.ts` | thêm `--color-series-1..3` và `--color-tier-low/mid/high` cho cả hai chế độ |
| `src/app/(station)/reports/page.tsx` | mới — đọc `?step=`, mỗi bước một biểu đồ |
| `src/constants/reportSteps.ts` | mới — ba màn con, cùng khuôn `PLANNER_STEPS` |
| `src/components/chart/ChartFrame.tsx` | mới — khung chung: tiêu đề, ô điều khiển, chú giải, nút bảng, rỗng/lỗi |
| `src/components/chart/BarRow.tsx` | mới — thanh ngang; dùng cho ① và ② |
| `src/components/chart/ColumnChart.tsx` | mới — cột đứng gom nhóm; dùng cho ③ |
| `src/components/chart/ChartTable.tsx` | mới — bảng số dùng chung |
| `src/components/reports/{MoProgress,SlotRanking,StepCounts}.tsx` | mới — ba màn |
| `src/services/reports.service.ts` · `src/hooks/reports/useReports.ts` · `src/types/reports.ts` · `src/utils/reports.ts` | mới |
| `src/constants/queryKeys.ts` | thêm `reportKeys` |
| `src/components/common/StationSidebar.tsx` | thêm nhóm `Báo cáo sản xuất` với ba mục con |

**Ba màn, ba đường dẫn:**

```
/reports                  ① Tiến độ MO
/reports?step=hourly      ② Năng suất theo giờ
/reports?step=steps       ③ MO từng bước
```

Theo đúng khuôn `?step=` mà các màn trạm và màn điều độ đang dùng, nên `NavGroup` tô sáng
mục đang mở mà không phải viết thêm gì, và `StepStrip` trong trang cũng dùng lại nguyên.

**`BarRow` dùng cho cả ① lẫn ②**, không viết hai loại thanh: ① một đoạn, ② một đoạn
đổi màu theo bậc cộng hai vạch mốc. Khác nhau ở dữ liệu truyền vào chứ không ở mã.
`ColumnChart` của ③ dùng lại nguyên kiểu `BarSegment` — hai hình khác hướng nhưng cùng
một cách mô tả dữ liệu.

**Không tự làm mới theo nhịp.** Bảng đang chạy đặt `refetchInterval` 10 giây vì có
người đứng chờ việc; ở đây người xem đang đọc một con số rồi nghĩ, kéo dữ liệu đổi dưới
tay họ chỉ làm mất chỗ.

**Cửa sổ tải của màn ② là HAI ngày**, không phải một: khung đầu ngày phải so được với
khung cuối ngày hôm trước, không thì mỗi sáng mũi tên chênh trống trơn.

### Frontend — để dành cho P4/P5, **chưa viết**

`BulletChart.tsx` (đặc tả Few) · `TimeColumnChart.tsx` (cột thời gian một chuỗi — tên
khác vì `ColumnChart.tsx` đã dùng cho ③) ·
`Sparkline.tsx` · `HourlyBoard.tsx` · `PlantOverview.tsx`.

Component trong `components/chart/` là **dùng chung** — màn hình khác cần biểu đồ thì
lấy lại, không viết mới.

---

## 6 · Việc KHÔNG làm trong đợt này

Ghi ra để không ai tưởng bị sót:

- **Không** OEE waterfall. Chỉ có `RUN`/`WAIT`, không có *chạy chậm* / *dừng vặt* —
  dựng waterfall từ dữ liệu này là dựng một hình trông đúng mà sai.
- **Không** Pareto "vì sao không đạt định mức". `hourly_output` chỉ có `note` chữ tự do;
  muốn thống kê được phải thêm `reason_code_id` (bảng `reason_code` đã có sẵn, chỉ thiếu
  cột nối). Làm sau, khi chạy thật vài tuần và biết lý do nào hay gặp.
  **Pareto lý do DỪNG MÁY thì làm được ngay** — `line_segment.hold_reason_code_id` đã có.
- **Không** dùng cột `note` ở màn Tổ trưởng. Nó là cột quan trọng nhất của màn **Thợ ở
  trạm** (P4), không phải của màn xếp hạng.
- **Không** lọc theo phòng ban hay chuyền — chưa ai yêu cầu.
- **Không** tự làm mới theo nhịp. Báo cáo là để đọc, không phải màn treo tường.
- **Không** đụng `le_pcs` sai ở backend (việc treo từ trước, không thuộc đợt này).
