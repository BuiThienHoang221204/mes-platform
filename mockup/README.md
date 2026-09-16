# MES v2.3 — Mockup từng phòng ban

Mở `index.html` bằng trình duyệt. Không cần build, không cần server.

Dựng từ `demo/BRD-v2-chot.md` (bản chốt đợt 1) và `demo/mes-v2-console.html`.
Mục tiêu là **duyệt luồng UX/UI**, không phải bản chạy thật: dữ liệu cố định,
nút bấm không đổi state (trừ vài chỗ ghi rõ bên dưới).

## Cấu trúc

```
mockup/
  index.html          khung: sidebar + topbar + vùng nội dung
  assets/app.css      design token kế thừa từ mes-v2-console.html
  assets/data.js      6 phòng ban · 13 vai · ma trận quyền §9b · dữ liệu mẫu
  assets/screens.js   27 màn hình — từng step của từng phòng ban
  assets/app.js       sidebar dựng theo vai, điều hướng, kiểm tra quyền
```

## Ba trục điều hướng

**1 · Đổi vai** (nút trong sidebar) — 13 vai: 6 phòng × 2 cấp + PLANNER.
Đổi vai thì **sidebar dựng lại**, không phải ẩn/hiện vài dòng. Đây là cách
nhanh nhất để thấy phân quyền §9b có hợp lý ngoài xưởng không.

**2 · Stepper trên đầu trang** — mỗi phòng ban là một luồng nhiều step, đi
đúng thứ tự người vận hành làm. Bấm qua lại được.

**3 · `Luồng toàn quy trình`** (sidebar) — bản đồ 6 trạm + hai đường quay lại.

## 27 màn hình

| Phòng ban | Step | Màn hình |
|---|---|---|
| Kho xuất | 0 | **Quét nhận** · Bàn giao · Xem phiếu |
| Setup | 1 | **Quét nhận** · Đang setup |
| QC | 2 | **Quét nhận** · PASS/FAIL |
| Bàn team leader | 3 | **Quét nhận** · Chờ vào chuyền |
| Sản xuất | 4 | **Quét nhận** · Chọn line · Bảng đang chạy → *rẽ 2 nhánh song song*: **Chuyền** (Sản lượng giờ · Chốt sổ SX) ‖ **Đóng thùng** (Bắt đầu·theo giờ · Kết thúc) |
| Kho nhập | 5 | **Quét nhận** · Hoàn thành |
| PLANNER | — | Tổng quan · Tạo MO · Sổ lệnh · Bảng đang chạy · Truy cứu MO |
| Xem chung | — | Bảng đang chạy · Step 4 (chỉ xem) · Luồng · Lịch sử & Truy cứu |

## Quyết định UX đã áp vào mockup

**Hàng đợi và ô quét nằm chung trang `Quét nhận`.** Đó là một việc chứ không
phải hai: nhìn xem lệnh nào đang chờ, rồi nhận đúng lệnh đó. Tách hai trang thì
người vận hành phải nhớ mã ở trang này để gõ ở trang kia.

Thanh quét đặt ngay đầu trang, gom đủ **ba đường vào của §1b** vào một ô: gõ
tay · đầu đọc USB bắn thẳng vào input · nút `Camera` cho máy không có đầu đọc.
Đầu đọc gõ xong thường bắn `Enter`, nên **Enter = bấm Nhận**; thiếu cái này thì
mỗi lần quét vẫn phải với tay bấm nút, mất hết cái lợi của đầu đọc.

Bấm một dòng trong hàng đợi sẽ **nạp mã vào ô quét** chứ không nhận luôn — §1b
đã bỏ nút Accept trên từng dòng vì nhiều đơn cùng lúc rất dễ bấm trúng MO bên
cạnh, nên thao tác thay thế cũng phải có chủ đích.

**Step 4 vẽ thành luồng rẽ nhánh, không phải dãy 1→7.** §7b chốt Đóng thùng
chạy *song song* trong Step 4: nút `Bắt đầu` mở ngay khi có ≥1 line vào
`Đang lắp ráp`, không chờ Chốt sổ SX. Vẽ bảy bước nối đuôi là bịa ra năm ràng
buộc không có, đồng thời giấu mất đúng cái ràng buộc có thật.

```
① Quét nhận → ② Chọn line → ③ Bảng đang chạy ─┬─ CHUYỀN ───── Sản lượng giờ → Chốt sổ SX ─┐
                          (bấm Đang lắp ráp)   └─ ĐÓNG THÙNG ─ Bắt đầu·theo giờ → Kết thúc ┴→ Step 5
                                                                                 ↑ chặn tới khi Chốt sổ xong
```

Ba bước đầu đánh số vì tuần tự thật. **Trong hai làn không đánh số** — số ngụ ý
thứ tự, mà hai làn chạy cùng lúc. Mỗi màn của làn ghi rõ mình thuộc nhánh nào và
mở được nhờ điều kiện gì. Màn `Bảng đang chạy` có panel *Hai nhánh của Step 4*
đặt hai timer cạnh nhau cho thấy chúng chồng thời gian (chuyền mở 09:24, đóng
thùng mở 09:31).

**Phản hồi khi quét nằm trong chính thanh quét**, một dòng ngay dưới ô nhập,
đổi màu xanh/đỏ theo kết quả. §1b.3 chốt *"quét sai trạm phải báo rõ lý do,
không im lặng"* nên không bỏ được — nhưng cũng không đáng một panel riêng. Dòng
đó đứng yên tới lần quét sau, khác với toast tắt sau 3 giây. Riêng đường **hỏng**
bắn thêm toast: tay người quét đang ở đầu đọc, mắt ở cái tem trên thùng hàng, đó
là đường không được phép bỏ sót.

**Trang `Quét nhận` chỉ một cột, hàng đợi chiếm cả bề ngang.** Hàng đợi là thứ
người ta nhìn lâu nhất ở trạm; bóp nó còn nửa màn hình để lấy chỗ cho chú thích
là đổi sai thứ. Hai nút cả lô của Kho nằm trên **header của chính danh sách** mà
chúng tác động, không phải một panel riêng bên cạnh. Quy tắc đọc mã (§1b.2,
§1b.3) gom về trang **Luồng toàn quy trình** — cùng một bộ luật cho cả sáu trạm,
đọc một lần là đủ, không lặp lại sáu lần.

**Sidebar là bản đồ quyền, không phải danh sách tính năng.** Trạm của mình liệt
kê đủ từng step; Step 4 ai cũng thấy nhưng gắn nhãn `chỉ xem` nếu vai không có
quyền ghi; ngoài ra không có mục nào khác. Vai `Bàn team leader` là chỗ duy nhất
mục Step 4 **không** có nhãn đó — ngoại lệ §9b.4.

**Mỗi màn hình mang theo lý do.** Các khối ghi chú dưới bảng là trích nguyên
quyết định trong BRD (vì sao QC FAIL về Kho, vì sao không gọi phần chênh là
"Thiếu", vì sao ba ô SL phải cộng đúng). Duyệt mockup mà không có lý do đi kèm
thì rất dễ chốt nhầm một màn hình nhìn gọn nhưng sai nghiệp vụ.

## Chỗ bấm thật được

- **Đổi vai** — dựng lại sidebar và chặn quyền thật.
- **Ô quét** — đọc mã đúng luật §1b.2: bỏ tiền tố trước `M`, tự sửa `O`→`0` và
  `I/L`→`1`, **từ chối** mã 7 chữ số và chuỗi chứa nhiều mã. Quét sai trạm báo
  rõ MO đang nằm ở đâu. Gõ `Enter` cũng nhận. Đã test đủ 8 dòng bảng §1b.2.
- **Nút `Camera`** — mở khung ngắm mockup, liệt kê đúng các MO đang trong hàng
  đợi của trạm để bấm thử. Bản chạy thật dùng `html5-qrcode` như
  `demo/mes-v2-console.html`.
- **Dòng phản hồi trong thanh quét** — đổi theo từng cú quét thật, lấy tên con
  hàng và SL từ MO thật. Gồm cả chống bắn hai lần: quét cùng mã hai lần liên
  tiếp ở một trạm thì lần hai bị chặn, nhưng đổi vai (đổi trạm) thì lại nhận.
- **Chốt sổ SX** (`Sản xuất › Chốt sổ SX`) — sửa 3 ô SL thì dòng tổng đổi ngay
  sang `khớp` / `đang dư` / `đang hụt`.
- **Kết thúc đóng thùng** — nhập vượt `SL đạt` thì báo chặn ngay.

## Còn treo — cần chốt trước khi code

Mockup dựng theo hiện trạng BRD, những chỗ sau BRD ghi là chưa chốt:

1. **Mã MO 6 chữ số do hệ thống cấp hay lấy từ ERP?** (§2.2, §10). Nếu từ ERP
   thì màn `PLANNER › Tạo MO` phải **bỏ hẳn khối tạo hàng loạt**.
2. **Mã QR dán lên hàng in ở đâu?** (§3, §10 #40). Đã bỏ bước In phiếu ở Kho,
   nên nếu ERP không in sẵn tem thì vẫn phải có chỗ in — chỉ là không ở bước này.
3. **Leader khác Member ở chỗ nào?** (§9b.8). Hiện hai cấp quyền y hệt nhau, đã
   tách sẵn vai nhưng chưa có màn hình nào phân biệt.
4. **Có cần vai chỉ-xem cho quản lý cấp trên không?** (§9b.8).
5. **Quyền trên `Lịch sử & Truy cứu`** — BRD không nói. Mockup đang cho mọi vai
   xem (gắn nhãn `chỉ xem` với vai không phải PLANNER). Cần xác nhận: tổ QC có
   được truy cứu MO đã qua tay tổ khác không?
