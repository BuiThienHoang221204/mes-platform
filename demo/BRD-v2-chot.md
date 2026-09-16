# MES Platform — Tài liệu nghiệp vụ v2 (Đã chốt đợt 1)

> Trạng thái: **Draft v2.23 — Cập nhật 2026-09-15 (Đổi tên: Bàn chờ → Bàn team leader · Đóng gói → Đóng thùng)**  
> Căn cứ: 1C/2C/3A/4A/5/6B/7A/8B/9A/11B/12B/14B/15A/16/17/18A/21A/22A/23A/25A + bỏ nút Complete + phiếu đơn giản + SX//Đóng thùng + vòng lặp  
> Demo đối chiếu: `demo/mes-v2-console.html`

---

## 0. Lịch sử thay đổi

### 0.1 v2.22 → v2.23 (mới nhất)

| # | Đổi gì | Vì sao |
|---|---|---|
| 1 | **`Bàn chờ` đổi tên thành `Bàn team leader`** (trạm 3, toàn tài liệu) | Gọi theo đúng tên người ngoài xưởng đang dùng. `Bàn chờ` nghe như một chỗ **để hàng nằm chờ**, trong khi đây là **bàn của team leader** — nơi có người đứng nhận và điều phối |
| 2 | **`Đóng gói` đổi tên thành `Đóng thùng`** (§7b, toàn tài liệu) | Từ v2.22 công đoạn này đếm bằng **thùng** và có quy cách pcs/thùng (§7b.2). Gọi là _đóng thùng_ thì tên việc khớp luôn với đơn vị đếm; _đóng gói_ rộng hơn, dễ hiểu lẫn sang dán tem / vào túi |
| 3 | Chỉ đổi **chữ hiển thị**, không đổi tên kỹ thuật | `packing` · `pack-start` · `PACK_START` · `RETURN_TO_BANCHO` giữ nguyên. Đổi tên kỹ thuật là phá dữ liệu đã lưu và nhật ký cũ, mà không được gì thêm — xem §9 mục 25A: nhật ký **append-only, giữ vĩnh viễn** |

> **Đổi được vì FE thật chưa dựng.** Hai cái tên này nằm rải khắp tài liệu và demo (156 chỗ). Sau khi có
> màn hình thật và người vận hành đã quen mắt thì đổi tên là chuyện tốn kém — đây là lúc rẻ nhất.

### 0.2 v2.21 → v2.22

| # | Đổi gì | Vì sao |
|---|---|---|
| 1 | **MO khai thêm `Quy cách` — bao nhiêu pcs một thùng** (§2, §7b.2) | Đơn hàng đặt bằng **PCS**, xưởng đóng thùng đếm bằng **THÙNG**. Không có con số quy đổi thì hai đơn vị không gặp nhau được. `0` = mặt hàng không đóng thùng |
| 2 | **THÙNG CUỐI của đơn được đóng THIẾU** (§7b.2) | `3.000 / 800 = 3,75`. Đơn nào không chia hết cho quy cách cũng có một thùng cuối không đầy — đó là **mặc định, không phải ngoại lệ**. Bắt thùng nào cũng phải đầy thì đơn không bao giờ đóng được: vĩnh viễn thiếu vài trăm cái cho đủ thùng, mà làm thêm cho đủ là **sản xuất dư** khách không đặt |
| 3 | **Panel `Đóng thùng theo giờ` — đếm thùng**, song song với `Sản lượng theo giờ` (§7b.2) | Ngoài xưởng người ta đếm thùng chứ không đếm từng con. Trong giờ **chỉ đếm thùng ĐẦY** |
| 4 | **Phân biệt `hàng lẻ chờ đóng` với `SL thiếu`** (§7b.2, §7.5) | Hai chuyện khác hẳn: _thiếu_ là **chưa làm ra được** → phải làm thêm → mở vòng mới; _lẻ_ là **đã làm ra rồi, chỉ chưa gom đủ một thùng** → không phải làm thêm gì. Gộp hai cái thì Nhập kho trả MO về Bàn team leader oan |
| 5 | **Tiến độ MO luôn tính bằng PCS**, thùng chỉ là cách đếm (§7b.2) | Mọi ràng buộc sẵn có (`đạt + hỏng + thiếu = mục tiêu vòng`, cộng dồn ở Nhập kho) đều chạy bằng pcs. Đưa đơn vị thô vào giữa dây số học đó là chỗ sinh ra lỗi |
| 6 | **Ghi lại ba hướng đã cân rồi loại** (§7b.2) | Ba hướng đó nghe rất hợp lý — đổi tiêu chí sang `SX đạt` · mang tồn lẻ sang vòng sau · làm tròn lên. Không ghi vì sao loại thì lần sau có người đề xuất lại đúng ba cái đó, và bàn lại từ đầu |
| 7 | **Câu hỏi mở #38 ghi thêm: v2.22 làm nó gần chốt nhưng CHƯA chốt** (§10) | Thùng cuối đóng thiếu ⇒ cuối vòng `SL đã đóng thùng` = `SX đạt`, ô nhập gần như thừa. Chỉ còn một tình huống giữ nó: hết ca mà hàng đạt còn nằm trên bàn. Phải hỏi xưởng, không tự suy |

### 0.3 v2.20 → v2.21

| # | Đổi gì | Vì sao |
|---|---|---|
| 1 | **Mỗi khung giờ ghi BA số: `Số người` · `Sản lượng yêu cầu` · `Sản lượng thực tế`** (§7.2b) | Một mình con số làm ra được không nói lên điều gì: 500 cái trong một giờ là nhanh hay chậm? Cùng 500 cái, 8 người khác hẳn 20 người; định mức 400 khác hẳn định mức 700. Thiếu hai số kia thì cuối ca không ai trả lời được vì sao hụt |
| 2 | **Hệ thống tự tính `Đạt %` và `Năng suất`, không cho nhập tay** (§7.2b) | Hai số này suy ra được từ ba số trên. Cho nhập tay là mở đường cho số liệu tự mâu thuẫn — và người ta sẽ điền số đẹp chứ không điền số thật |
| 3 | **Ô nhập cũ tên `SL` đổi thành `Sản lượng thực tế`** (§7.2b) | Giờ có hai loại sản lượng cạnh nhau trên cùng một dòng. `SL` trống nghĩa thì người ghi phải đoán, mà đoán sai thì số nằm nhầm cột |

### 0.4 v2.19 → v2.20

| # | Đổi gì | Vì sao |
|---|---|---|
| 1 | **Thêm §9b — Phân quyền**, chốt câu hỏi mở #26 | Sáu phòng ban, mỗi phòng Leader + Member. Không chốt thì BE không biết chặn ai ở đâu, mà càng để lâu càng khó sửa vì tài khoản đã phát ra rồi |
| 2 | **Kho xuất (0) và Kho nhập (5) tách thành HAI phòng ban** | Trước gộp một vai `KHO`. Đây là **hai kho vật lý khác nhau** — kho vật tư và kho thành phẩm, hai toà nhà, hai tổ người. Gộp thì người giao vật tư tự nhận luôn thành phẩm của chính lô mình giao, mất hẳn lớp đối soát |
| 3 | **Đóng thùng thuộc phòng Sản xuất**, không phải phòng riêng | Nó chạy song song trong Step 4 (§7b), không phải một step |
| 4 | **Bàn team leader có FULL quyền trên Step 4**, kể cả Đóng thùng | Bàn team leader đứng ngay trước chuyền, thực tế hai tổ làm lẫn nhau |
| 5 | **Mọi phòng ban đều View được Step 4 — gồm cả Đóng thùng — và Bảng đang chạy** | Sản xuất quyết định tiến độ; Đóng thùng là số cuối trước khi hàng về kho. Giấu đi thì mỗi tổ mù về công đoạn trước sau, gọi điện hỏi nhau nhiều hơn |

### 0.5 v2.18 → v2.19

| # | Thay đổi | Vì sao |
|---|---|---|
| 1 | **Bảng Timer từng bước cộng dồn thời gian qua MỌI VÒNG**, kèm chú thích `n vòng` (§9) | Trước chỉ đọc vòng hiện tại, nên MO qua Setup hai lần mà vòng cuối bắt đầu từ Bàn team leader thì cột Setup hiện `—`. Nhìn vào tưởng chưa từng setup |
| 2 | **Truy cứu: mỗi vòng một bảng `Đi qua các bước`**, không chỉ vòng đang chạy (§9) | Vòng cũ coi như mất dấu: không biết ai nhận, ai đóng, mất bao lâu. Giờ vòng nào cũng xem lại được đủ |
| 3 | **Dòng `4 · Sản xuất` bấm được**, bung ra **năng suất từng line** và **sản lượng giờ của chính vòng đó** (§9) | Sản xuất là bước duy nhất có nhiều việc bên trong: mấy line chạy, line nào dừng vì gì, mỗi giờ ra bao nhiêu. Nén vào một con số thời lượng là mất sạch |
| 4 | **Sản lượng giờ đối soát với `SX đạt` của vòng**, không phải SL đã đóng thùng của cả MO (§7.2b) | Sản lượng giờ ghi theo vòng thì phải so với số của vòng đó. So với tổng cả đơn là lệch ngay khi MO chạy từ vòng hai |
| 5 | **Cột `Bắt đầu từ` đọc thẳng nơi vòng bắt đầu**, không suy từ các bước đã đi (§6b.4) | Cách suy cũ chỉ đúng với vòng đã xong. Vòng vừa mở chưa nhận bước nào luôn bị đoán nhầm thành `Bàn team leader` — kể cả khi QC FAIL vừa trả nó về Kho |
| 6 | **Con số trên thanh trạm Kho đếm cả lệnh đã nhận nhưng chưa bàn giao** (§3) | Badge hiện `0` trong khi kho còn lệnh nằm đó chờ giao |
| 7 | **Bỏ `KHO_PRINT` khỏi danh sách action**, bỏ `printedAt` khỏi §6b.2 (§9, §6b.2) | Dọn nốt dấu vết của thao tác In phiếu đã bỏ ở v2.18 |

### 0.6 v2.17 → v2.18

| # | Thay đổi | Vì sao |
|---|---|---|
| 1 | **Bỏ thao tác `In phiếu` ở bước Kho** (§3). Nhận lệnh xong là **Bàn giao** luôn | Bớt một lần bấm cho mỗi MO. Với lô 50 lệnh một ca là bớt 50 thao tác — mà cái bấm đó không quyết định điều gì: in hay không in thì hàng vẫn xuống xưởng, và hệ thống vẫn chặn Setup nếu chưa bàn giao |
| 2 | **Bỏ luôn `printedAt` · `printCount` và ràng buộc “chưa in thì không bàn giao”** (§3) | Không còn thao tác in thì hai ô này không có gì để ghi. Ràng buộc cũ chỉ có nghĩa khi in là một bước bắt buộc |
| 3 | **Giữ `Xem phiếu`** nhưng chỉ để xem hoặc in bằng trình duyệt, hệ thống không ghi sổ (§3) | Vẫn cần nhìn phiếu để đối chiếu mã và số lượng, nhưng đó là hành động tra cứu chứ không phải một bước của quy trình |

> **Câu hỏi kéo theo — đã thành #40 ở §10:** bỏ in ở Kho thì **mã QR dán lên hàng đến từ đâu**? Nếu tem
> QR do ERP hoặc bộ phận khác in sẵn thì không sao; nếu không thì phải có chỗ nào đó in, chỉ là không phải
> ở bước này.

### 0.7 v2.16 → v2.17

| #   | Thay đổi                                                                                         | Vì sao                                                                                                                                                                                       |
| --- | ------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | **Thêm câu hỏi mở #39 — có cần cột `Hiện trạng MO`?** kèm nguyên phương án 5 chặng đã phác (§10) | Đã phân tích kỹ ngày 2026-09-12 rồi quyết định **chưa làm**. Không ghi lại thì lần sau bàn lại từ đầu — mà vấn đề gốc _(ô báo `Hoàn thành` xanh trong khi MO còn thiếu hàng)_ thì vẫn còn đó |
| 2   | **#31 ghi thêm hệ quả hiển thị** (§10)                                                           | Ngưỡng dừng máy không chỉ là chuyện tự trả MO về Bàn team leader — nó còn quyết định khi nào bảng được báo đỏ. Chốt #31 là chốt luôn cho #39                                                         |
| 3   | **Đồng bộ tên cột với demo**: `Hiện trạng Line`, `Ghi chú đóng thùng`, bảng `Các vòng`             | Tài liệu và demo phải gọi cùng một thứ bằng cùng một tên, nếu không lúc bàn giao mỗi bên hiểu một kiểu                                                                                       |

### 0.8 v2.15 → v2.16

| #   | Thay đổi                                                                                                                                     | Vì sao                                                                                                                                                                                     |
| --- | -------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 1   | **Trạng thái line `Đang tiến hành` đổi tên thành `Đang lắp ráp`** — nhãn ở bảng, chữ trên nút bấm, nhật ký và mọi câu thông báo (§15A, §7.2) | Gọi đúng việc đang diễn ra ở chuyền. _"Đang tiến hành"_ là chữ hành chính, không nói được máy đang làm gì; _"Đang lắp ráp"_ thì tổ trưởng đọc là hiểu ngay                                 |
| 2   | **Cột `Hiện trạng` đổi tên thành `Hiện trạng Line`** (§7.2)                                                                                  | Nói rõ ô này là trạng thái **của line**, không phải của MO — enum `run_status` §15A vốn là của line                                                                                        |
| 3   | **Cột `Lý do đóng thùng` đổi tên thành `Ghi chú đóng thùng`** (§6b.4, §9)                                                                        | Đóng thùng thường không có "lý do" gì để giải thích — ô này là chỗ ghi chú tự do (`Đủ`, `thiếu thùng`, `chờ tem`). Gọi là _lý do_ khiến người nhập tưởng bắt buộc phải có sự cố mới được ghi |

> Đổi tên hiển thị, **không đụng dữ liệu**: enum `run_status` vẫn là `WAIT / RUN / DONE` (§15A, `DB-DESIGN.md`), luồng nghiệp vụ và mọi cách tính giờ giữ nguyên.

### 0.9 v2.14 → v2.15

| #   | Thay đổi                                                                                                                                             | Vì sao                                                                                                                                                                             |
| --- | ---------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | **Bảng `Các vòng đã chạy` đổi tên thành `Các vòng` và hiện cả vòng đang chạy**, dòng cuối gắn badge `đang chạy`, các ô điền dần theo tiến độ (§6b.4) | Bảng cũ chỉ liệt kê vòng **đã đóng sổ**. Trong cửa sổ _"đã chốt sổ SX → chưa nhập kho"_ — đúng lúc người ta cần xem hỏng/thiếu vừa khai — bấm truy cứu **không thấy dòng nào**     |
| 2   | **Vòng cuối của MO hoàn thành cũng được chốt sổ** vào `stepsHistory` (§6b.4)                                                                         | Trước đây chỉ vòng bị trả lại mới ghi sổ. MO xong ngay vòng 1 thì bảng truy cứu **trống trơn**; MO chạy 3 vòng thì chỉ thấy 2                                                      |
| 3   | **Cột `Sản lượng` ở Bảng đang chạy rút còn một dòng** — `Đạt 9.000/10.000`, bỏ dòng tách `hỏng 300 · thiếu 700 → bù 1.000` (§7.2)                    | Bảng đang chạy là bảng **treo tường** — liếc để biết đơn nào chưa đủ. Chi tiết hỏng/thiếu/lý do là câu hỏi thứ hai, và giờ truy cứu MO trả lời được nó ở **mọi thời điểm** (mục 1) |

### 0.10 v2.13 → v2.14

| #   | Thay đổi                                                                                                                                            | Vì sao                                                                                                                                                                                                                          |
| --- | --------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | **Thêm ô `SL thiếu`** ở form chốt Sản xuất — người vận hành khai, hệ thống không tự suy ra nữa (§7.5)                                               | Trước đây `thiếu` là số hệ thống tính ngầm `mục tiêu − đạt − hỏng`, người khai không nhìn thấy nên không ai xác nhận nó đúng                                                                                                    |
| 2   | **`SL đạt + SL hỏng + SL thiếu` phải cộng ĐÚNG BẰNG mục tiêu vòng** (§7.5)                                                                          | Chốt đối soát: mỗi PCS giao xuống chuyền phải rơi vào đúng một trong ba nhóm. Lệch nghĩa là có hàng không ai khai — chặn, không cho chốt sổ. Thay cho ràng buộc cũ lỏng hơn (`đạt + hỏng ≤ mục tiêu`)                           |
| 3   | **Form hiện tổng sống `Σ 10.000 — khớp` / `Σ 9.800/10.000 — hụt 200`** ngay khi gõ (§7.5)                                                           | Không bắt người vận hành bấm Xác nhận rồi mới biết mình gõ lệch                                                                                                                                                                 |
| 4   | **Chốt sổ Sản xuất chỉ một lần cho mỗi vòng** (§7.5)                                                                                                | Gọi lại lần hai sẽ ghi đè SL đã khai mà không để lại dấu vết — nay chặn hẳn                                                                                                                                                     |
| 5   | **Bảng Các vòng đã chạy: mỗi lý do một cột riêng**, thêm cột `SL thiếu` (§6b.4)                                                                     | Nhét lý do xuống dưới con số làm cột số hết đọc lướt được, mà chữ cũng bị co nhỏ khó đọc. Số về cột số, chữ về cột chữ                                                                                                          |
| 6   | **Cột `Sản lượng` ở Bảng đang chạy đổi cách hiện**: `Đạt 9.000/10.000` + `hỏng 500 · thiếu 500 → bù 1.000 ở vòng sau`, bỏ nhãn `Thiếu 1.000` (§7.2) | Từ _"thiếu"_ nay đã có nghĩa riêng — SL không làm ra được. Cột này lại gọi phần chênh `mục tiêu − đạt` (gồm cả hỏng lẫn thiếu) là "Thiếu 1.000" trong khi người vận hành vừa khai _thiếu 500_ — đọc vào tưởng hệ thống tính sai |

### 0.11 v2.12 → v2.13

| #   | Thay đổi                                                                 | Vì sao                                                                                                                                                             |
| --- | ------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 1   | **Tách `Lý do hỏng` và `Lý do thiếu`** ở bước Sản xuất (§7.5)            | Hỏng 500 vì lỗi khuôn, thiếu 1.000 vì chờ bù liệu — hai chuyện khác nhau. Gộp một ô thì mất một nửa thông tin                                                      |
| 2   | **Lý do thiếu là bắt buộc** khi làm không đủ mục tiêu vòng (§7.5)        | Làm thiếu mà không hỏng cái nào là chuyện rất thường (hết liệu, đổi ca). Trước đây chỉ hỏi lý do khi có hàng hỏng nên lô thiếu không ai giải thích                 |
| 3   | **Tách cột `Tiến độ SL` và `KPI thời gian`** ở bảng Timer từng bước (§9) | Một cột không thể vừa trả lời _"có kịp giờ không"_ vừa trả lời _"có đủ hàng không"_. Gộp lại thì chữ `Đạt` bị đọc thành "xong đơn rồi" trong khi MO còn thiếu hàng |
| 4   | **Bảng Các vòng đã chạy: cột `Bắt đầu từ`** thay `Kho nhận` (§6b.4)      | Vòng quay về Bàn team leader không hề đi qua Kho, nhưng cột cũ vẫn lặp lại mốc giờ Kho của vòng 1 cho mọi vòng                                                             |
| 5   | **Tách `SX đạt` và `Đã đóng thùng`** thành hai cột (§6b.4)                 | Cột cũ tên là "SL đạt" nhưng hiện SL đã đóng thùng — không thấy được chuyền làm ra bao nhiêu                                                                         |

### 0.12 v2.11 → v2.12

| #   | Thay đổi                                                   | Vì sao                                                                                                                                                               |
| --- | ---------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | **MO thiếu SL trả về `Bàn team leader`**, không về Kho (§6b)       | Máy đã setup đúng, hàng đã qua QC — chỉ là chưa làm đủ số. Bắt in lại phiếu và setup lại từ đầu là thừa. **QC FAIL vẫn về Kho** vì setup sai thì phải làm lại từ gốc |
| 2   | **`SL hỏng` chuyển từ Đóng thùng sang Sản xuất** (§7.5, §7b) | Chuyền mới là chỗ phát hiện hàng lỗi. Hàng xuống tới đóng thùng là hàng đã đạt, nên ở đó luôn đạt — chỉ còn câu hỏi _đóng được bao nhiêu_                              |
| 3   | **Quét QR thay cho bấm Accept ở mọi bước** (§1b)           | Nhiều đơn cùng lúc thì bấm Accept rất dễ trúng nhầm MO bên cạnh. Bỏ luôn nút Accept trên từng dòng hàng đợi                                                          |
| 4   | **Mã MO đổi sang `M` + 6 chữ số** (§2.1, §2.2)             | Mã thật ngoài xưởng là `M068820`, không phải `F3-25/06-001` như ví dụ cũ                                                                                             |
| 5   | **Camera quét QR** cho máy không có đầu đọc (§1b)          | Máy tính bảng / điện thoại ngoài chuyền dùng luôn camera, không cần mua đầu đọc                                                                                      |

### 0.13 v2.10 → v2.11

Tách `SL đạt` / `SL hỏng` · **thời gian yêu cầu chia theo SL của vòng** · sản lượng giờ **gắn ngày** · xem lại sản lượng giờ trong truy cứu MO · lưu `Lý do đóng thùng` vào bản ghi vòng.

### 0.14 v2.9 → v2.10

Sửa 8 chỗ tự mâu thuẫn: KPI đổi từ so **năng suất** sang so **thời gian** · bỏ chia SL theo line · `21A` lấy line chạy lâu nhất · chốt 3 trạng thái + badge `ĐANG DỪNG` · bỏ `deadline`. **Thêm khái niệm VÒNG CHẠY** (§6b).

---

## 1. Tổng quan quy trình

```
Tạo MO (lẻ + hàng loạt 10–100)
  ↓ Submit
Kho nhận → Bàn giao
  ↓
Step1 Setup máy
  ↓
Step2 QC ──────────── FAIL ──────────────────────┐
  ↓ PASS                                         │
Step3 Bàn team leader ◄──────────────────────┐           │
  ↓                                  │           │
Step4 Sản xuất (14 line) + Đóng thùng song song    │
      ├─ SX:       Chờ xử lý ⇄ Đang lắp ráp → Hoàn thành (SL đạt + SL hỏng)
      └─ Đóng thùng: Bắt đầu → Kết thúc (SL đã đóng)
  ↓ (cả SX và Đóng thùng xong)         │           │
Step5 Nhập kho                       │           │
  ├─ đủ SL  → COMPLETED              │           │
  └─ thiếu ─────────────────────────►┘           │
                                                 ▼
                                               Kho
```

**Hai đường quay lại, khác nhau ở nguyên nhân:**

| Nguyên nhân                  | Về đâu      | Vì sao                                                                      |
| ---------------------------- | ----------- | --------------------------------------------------------------------------- |
| Thiếu SL · line dừng quá lâu | **Bàn team leader** | Máy setup đúng, hàng đã qua QC — chỉ thiếu số. Không in lại phiếu           |
| **QC FAIL**                  | **Kho**     | Setup sai → phải làm lại từ gốc: in phiếu mới, Setup chỉnh máy, QC kiểm lại |

Mỗi bước có timer riêng. SX và Đóng thùng trong Step4 có 2 timer song song.

---

## 1b. Quét QR — cách nhận ở mọi bước

> **Mọi bước đều nhận bằng quét, không bấm Accept.** Nút Accept trên từng dòng hàng đợi **đã bỏ** — nhiều đơn cùng lúc thì bấm rất dễ trúng nhầm MO bên cạnh.

### 1b.1 Ba đường vào, một bộ kiểm tra

```
Camera (nút icon trên máy)  ┐
Đầu đọc QR cắm cổng USB     ├──► đọc mã ──► nhận theo TRẠM đang mở
Gõ tay vào ô nhập           ┘
```

Không có đầu đọc thì **bấm vào dòng trong hàng đợi để nạp mã vào ô quét** rồi bấm `Nhận` — vẫn là thao tác có chủ đích, không phải một cú bấm là xong.

### 1b.2 Định dạng mã quét

Mã MO là **`M` + đúng 6 chữ số**. Khi quét luôn có ký tự đứng trước do đầu đọc chèn vào, nên **bỏ qua mọi thứ trước chữ `M`**.

| Quét vào                | Kết quả     | Ghi chú                                      |
| ----------------------- | ----------- | -------------------------------------------- |
| `XM068820`              | `M068820`   | tiền tố 1 ký tự — trường hợp thật            |
| `]Q1M076730`            | `M076730`   | tiền tố 3 ký tự vẫn chạy                     |
| `xm068820` + xuống dòng | `M068820`   | chữ thường, ký tự điều khiển tự bỏ           |
| `XMO68820`              | `M068820`   | gõ chữ `O` thay số `0` → tự sửa              |
| `XM0688201`             | **từ chối** | 7 chữ số — **không cắt bừa** thành `M068820` |
| `XM068820M076730`       | **từ chối** | nhiều mã trong một lần quét                  |

> Hai chỗ từ chối là có chủ ý. Cắt bừa mã 7 số ra một mã 6 số **có thật** là loại lỗi không ai phát hiện được. Gặp nhiều mã thì thà bắt quét lại còn hơn đoán sai đơn.

### 1b.3 Quy tắc kích hoạt

- **Mã QR chỉ nói MO nào**, không nói bước nào. Bước được kích hoạt lấy từ **màn hình/thiết bị đang mở** — máy đặt ở trạm QC thì quét là QC nhận.
- **Chống bắn hai lần:** đầu đọc hay bắn trùng, nên bỏ qua lần trùng trong 2 giây. Khoá theo **mã + trạm**, không chỉ theo mã — cùng một MO quét tiếp ở trạm kế bên phải ăn ngay.
- **Quét sai trạm thì báo rõ lý do**: _"đang ở QC"_, _"đã nhận ở trạm này rồi"_, _"không có trong hệ thống"_ — không im lặng.
- **Bước cần nhập thêm dữ liệu thì quét chỉ thay được thao tác nhận.** QC vẫn phải chọn PASS/FAIL, Sản xuất vẫn phải nhập SL đạt/hỏng, Đóng thùng vẫn phải nhập SL.

### 1b.4 Kho vẫn giữ thao tác hàng loạt

Riêng Kho có **cả hai**: quét từng lệnh khi cần chính xác, và `Accept tất cả` / `Bàn giao tất cả` khi phát lệnh đầu ca — vì §7A chốt là Kho phải xử được 10–100 lệnh một lúc.

---

## 2. MO — Manufacturing Order

### 2.1 Field

| Field                  | Mô tả                                                      | Chốt                                                 |
| ---------------------- | ---------------------------------------------------------- | ---------------------------------------------------- |
| moCode                 | Mã duy nhất, có QR                                         | **`M` + 6 chữ số** (`M068820`). Unique toàn hệ thống |
| product                | Tên con hàng                                               | 1 MO = 1 sản phẩm                                    |
| quantity               | Số lượng kế hoạch                                          | >0, **không đổi qua các vòng**                       |
| unit                   | PCS ...                                                    | —                                                    |
| pcsPerBox              | Quy cách — bao nhiêu pcs một thùng. `0` = không đóng thùng | Khoá cứng sau Submit như `quantity` |
| requiredProductionTime | **Thời gian lắp ráp yêu cầu — CHỈ áp dụng cho Step4** [3A] | giây. **Chia theo SL của vòng**, xem §7.3            |
| status / currentStep   | Trạng thái                                                 | tách riêng                                           |
| round                  | Vòng chạy hiện tại, bắt đầu 1                              | tăng mỗi lần trả lại                                 |
| qtyDone                | **SL đã đóng thùng** cộng dồn các vòng trước                 | 0 khi tạo. **Không cộng SL hỏng**                    |
| qtyNgTotal             | **SL HỎNG** cộng dồn — lấy từ bước **Sản xuất**            | dùng tính tỷ lệ phế                                  |
| qtyRemain              | `= quantity − qtyDone`, luôn ≥ 0                           | mục tiêu của vòng hiện tại                           |

> **Bỏ `deadline`.** Ràng buộc thời gian duy nhất là `requiredProductionTime`, chỉ dùng cho Step4.

### 2.2 Tạo MO

- **1C:** tạo lẻ và tạo hàng loạt 10–100 MO/lần.
- **2C:** nhập tay và import CSV 4 cột `Mã, Tên con hàng, Số lượng, TG yêu cầu Step4`.
- **Mã chạy liên tục:** tạo hàng loạt nhập **số bắt đầu** + số lượng → `M067690`, `M067691`, … Không còn kiểu tiền tố + 3 chữ số.
- Mã sai định dạng thì **chặn ngay**, cả khi nhập tay lẫn khi import.
- Tạo hàng loạt chạy trong transaction: trùng 1 mã → không tạo dòng nào.
- **4A:** sau Submit **khóa cứng** `moCode/product/quantity/requiredProductionTime`. Nhập sai → `CANCELLED` + tạo MO mới. Không hard delete.

> **CẦN CHỐT:** số chạy 6 chữ số do **hệ thống tự cấp** hay lấy từ **ERP bên ngoài**? Nếu lấy từ ERP thì không được tự sinh — chỉ nhập tay hoặc import, và phần tạo hàng loạt phải bỏ.

### 2.3 Trạng thái MO

`DRAFT → SUBMITTED → PROCESSING → COMPLETED` (có `CANCELLED` kèm lý do)

MO chưa hoàn thành **không đổi status** — vẫn `PROCESSING`, chỉ `round` tăng và `currentStep` về **3 (Bàn team leader)** hoặc **0 (Kho)** tuỳ nguyên nhân.

---

## 3. Kho — Bàn giao xuống xưởng [6B][7A]

Nhận lệnh rồi bàn giao cho Setup. Cũng là nơi tiếp nhận MO **bị QC FAIL**.

```
MO SUBMITTED + MO quay về do QC FAIL
  ↓ Kho thấy QUEUE danh sách chờ
  ↓ Quét QR để nhận từng lệnh, hoặc Accept cả lô
  ↓ Bàn giao → Setup [6B: bắt buộc ghi nhận trên hệ thống]
      [7A: bàn giao cả lô bằng một nút]
```

- Ghi riêng mỗi MO: `acceptedBy/At`, `handedOverBy/At`. **Đúng hai thao tác: nhận và bàn giao.**
- **Không còn bước In phiếu.** Bớt một lần bấm cho mỗi MO — lô 50 lệnh một ca là bớt 50 thao tác. Cái
  bấm đó không quyết định điều gì: in hay không in thì hàng vẫn xuống xưởng, và hệ thống vẫn chặn Setup
  nếu chưa bàn giao.
- **`Xem phiếu` vẫn còn** nhưng chỉ để xem hoặc in bằng trình duyệt — **hệ thống không ghi sổ**. Đây là
  hành động tra cứu, không phải một bước của quy trình.
- **Phiếu [5]:** 1 tờ đơn giản — **MO Code nổi bật** + Tên con hàng + Số lượng + TG yêu cầu Step4 + QR.
  Không cần ký nhận.
- **MO quay về do QC FAIL:** phiếu ghi rõ **SL còn thiếu** và **số lần trả lại**, không hiện như lệnh mới.
- **Chặn:** chưa `HANDOVER` thì Setup không nhận được.
- **Con số trên thanh trạm Kho** đếm **cả hai nhóm**: lệnh chưa ai nhận, và lệnh đã nhận nhưng chưa
  bàn giao. Chỉ đếm nhóm đầu thì badge hiện `0` trong khi kho còn hàng nằm đó chờ giao.

> **Còn treo — §10 #40:** bỏ in ở Kho thì **mã QR dán lên hàng đến từ đâu**? Tem do ERP hoặc bộ phận khác
> in sẵn thì không sao; nếu không thì vẫn phải có chỗ in, chỉ là không phải ở bước này.

---

## 4. Step1 — Setup máy [8B][9A]

```
Quét QR (hoặc gõ mã) → check tồn tại + đã HANDOVER
  ├─ sai → chặn, báo rõ lý do [9A]
  └─ đúng → nhận ngay → Timer Step1 START
Setup làm xong — KHÔNG bấm Complete
QC quét cùng mã → Step1 tự COMPLETED (completedAt = QC.acceptedAt)
```

History ghi `STEP1_ACCEPT` và `STEP1_AUTO_COMPLETE` kèm `triggeredBy`.

**Quy tắc step 1→3:** không có nút Complete riêng, **Step N Complete khi Step N+1 nhận**. Step4 và Step5 có nút riêng để đo timer song song.

---

## 5. Step2 — QC [23A]

- Quét QR để nhận → Step1 auto-complete, Timer Step2 START.
- **PASS** → sang Step3. **FAIL** → bắt buộc `Failure Reason`, ghi `QC_FAIL`, **chuyển về Kho chạy vòng mới**.
- **Vì sao QC FAIL phải về Kho chứ không về Bàn team leader:** FAIL nghĩa là setup sai. Cho về Bàn team leader thì MO **nhảy qua luôn Setup và QC** — hàng lỗi setup đi thẳng vào chuyền mà không ai sửa máy.
- **Kết quả QC gắn theo vòng.** Sang vòng mới, kết quả cũ cất vào `qcHistory` rồi xoá.

---

## 6. Step3 — Bàn team leader

Quét QR để nhận → Step2 auto-complete, Timer Step3 START. Complete khi Step4 nhận.

**Đây cũng là nơi MO thiếu SL quay về.** Máy đã setup đúng, hàng đã qua QC, chỉ là chưa làm đủ số — nên không phải in lại phiếu, không setup lại, không QC lại. Vòng mới **mở sẵn bước Bàn team leader**, MO nằm luôn ở hàng đợi Sản xuất chờ Line Leader quét.

---

## 6b. VÒNG CHẠY — mô hình cốt lõi

### 6b.1 Khi nào sinh vòng mới, và về đâu

| Nguyên nhân                       | Về          | Ghi nhận                                 |
| --------------------------------- | ----------- | ---------------------------------------- |
| Nhập kho thiếu SL                 | **Bàn team leader** | `MO_PARTIAL` + `RETURN_BANCHO`           |
| Line dừng quá lâu không khắc phục | **Bàn team leader** | `RETURN_BANCHO`                          |
| QC FAIL                           | **Kho**     | `QC_FAIL` + `RETURN_KHO`, badge `Rework` |

Tất cả đi qua **một hàm duy nhất** `moVongMoi(mo, lý do, bướcVề)` để `round`, badge và history luôn nhất quán.

### 6b.2 Vòng mới làm gì

```
round += 1
qtyDone    += SL ĐÃ ĐÓNG THÙNG của vòng vừa xong
qtyNgTotal += SL HỎNG của vòng vừa xong        ← lấy từ bước Sản xuất
qtyRemain   = quantity − qtyDone                (luôn ≥ 0)
status vẫn PROCESSING
```

**Chốt sổ rồi dọn để vòng mới bắt đầu trắng:**

| Dữ liệu              | Xử lý                                                      |
| -------------------- | ---------------------------------------------------------- |
| `steps{}`            | snapshot vào `stepsHistory[]` rồi **reset rỗng**           |
| `qc`                 | snapshot vào `qcHistory[]` rồi **xoá**                     |
| `packing` · `sx`     | snapshot vào `packingHistory[]` rồi **reset**              |
| `runs[]`, `hourly[]`, `packHourly[]` | **giữ nguyên**, mỗi bản ghi có `round` riêng nên không lẫn |

**Khác nhau giữa hai đích đến:**

|                                             | Về Bàn team leader                               | Về Kho                                  |
| ------------------------------------------- | ---------------------------------------- | --------------------------------------- |
| `currentStep`                               | **3**                                    | **0**                                   |
| `steps[3]` của vòng mới                     | **mở sẵn** → vào thẳng hàng đợi Sản xuất | rỗng                                    |
| `kho.acceptedAt / handedOverAt`             | **giữ nguyên** — hàng vẫn ở xưởng        | **xoá** — phải Accept và bàn giao lại   |
| Phải qua Setup & QC lại                     | **Không**                                | **Có**                                  |

> **Vì sao phải reset `steps`:** `steps[5].acceptedAt` của vòng cũ sẽ khiến MO **không bao giờ vào lại được hàng đợi Nhập kho** — đóng thùng xong cũng kẹt.

### 6b.3 Mục tiêu SL của vòng

```
mục tiêu vòng hiện tại = qtyRemain = quantity − qtyDone
```

- Sản xuất chặn theo mục tiêu vòng: `SL đạt + SL hỏng ≤ qtyRemain`.
- Đóng thùng chặn theo **SL đạt của Sản xuất**: `SL đóng thùng ≤ SL đạt`.
- `COMPLETED` khi `qtyDone + SL đã đóng thùng ≥ quantity`.
- **SL hỏng không tính là đã xong** → phải làm bù ở vòng sau.

> Nếu so với `quantity` thì vòng 2 đóng đúng 1.000 vẫn bị coi là thiếu → lặp vô hạn; đóng lại 9.000 thì `qtyDone` vượt `quantity` → hiển thị **số âm**.

### 6b.4 Hiển thị

MO quay về **không hiển thị như lệnh mới**. Ở mọi nơi hiện `Đã xong 9.000 / Còn 1.000` lấy từ `qtyDone` và `qtyRemain` — **không tự trừ lại** — kèm badge `Còn 1.000/10.000`, `Trả lại lần n`, `Về Bàn team leader — làm tiếp 1.000`, và `Rework` nếu do QC FAIL.

Bảng **Các vòng** (trong truy cứu MO) ghi mỗi vòng một dòng — **kể cả vòng đang chạy**:

| Vòng               | Bắt đầu từ      | Nhập kho xong | SX đạt | SL hỏng | SL thiếu | Đã đóng thùng | Lý do hỏng  | Lý do thiếu | Ghi chú đóng thùng | Lý do trả lại                         |
| ------------------ | --------------- | ------------- | ------ | ------- | -------- | ----------- | ----------- | ----------- | ---------------- | ------------------------------------- |
| Vòng 1             | Kho · 22:25     | 22:26         | 8.000  | 500     | 1.500    | 8.000       | Lỗi ép nhựa | Chờ bù liệu | Đủ               | Còn 2.000 — về Bàn team leader                |
| Vòng 2 `đang chạy` | Bàn team leader · 22:34 | —             | 1.983  | —       | 17       | —           | —           | Hết ca      | —                | _vòng chưa chốt sổ — số còn thay đổi_ |

- **`Bắt đầu từ` đọc thẳng nơi vòng đó bắt đầu**, ghi lại ngay lúc mở vòng (`0` Kho · `3` Bàn team leader), không suy từ các bước đã đi. Cách suy cũ chỉ đúng với vòng đã chạy xong: **vòng vừa mở chưa nhận bước nào luôn bị đoán nhầm thành `Bàn team leader`** — kể cả khi QC FAIL vừa trả nó về Kho. Nhìn vào là thấy vòng nào đi lại từ đầu, vòng nào chỉ chạy tiếp.
- **`SX đạt` và `Đã đóng thùng` tách riêng.** Về nguyên tắc hai số bằng nhau vì hàng tới đóng thùng là hàng đã đạt; chúng chỉ khác khi **đóng thùng chưa đóng hết hàng đạt** (hết thùng, hết ca).
- **Số về cột số, chữ về cột chữ.** Bốn cột số (`SX đạt` · `SL hỏng` · `SL thiếu` · `Đã đóng thùng`) đứng liền nhau để đọc lướt và cộng nhẩm được; ba cột lý do (`hỏng` · `thiếu` · `đóng thùng`) đứng liền nhau ở sau. Nhét lý do xuống dưới con số thì cột số mất khả năng đọc lướt, mà chữ cũng bị co nhỏ khó đọc.
- **Ba cột số đầu cộng lại đúng bằng mục tiêu vòng** — `8.000 + 500 + 1.500 = 10.000`. Nhìn một dòng là đối soát được ngay.
- **Vòng đang chạy cũng có dòng**, gắn badge `đang chạy`, các ô điền dần theo tiến độ: chốt sổ SX xong thì có `SX đạt / SL hỏng / SL thiếu` và hai cột lý do; đóng thùng xong thì có `Đã đóng thùng`; nhập kho xong thì dòng chốt lại. Cột `Lý do trả lại` trong lúc đó ghi _vòng chưa chốt sổ — số còn thay đổi_ để không ai tưởng đây là số đã khóa.
- **Vòng cuối cũng được ghi sổ.** `stepsHistory` nhận một dòng cả khi MO trả lại (vòng mới) lẫn khi MO hoàn thành, nên truy cứu luôn thấy đủ mọi vòng — MO xong ngay vòng 1 vẫn có một dòng.
- **Ghi chú đóng thùng** là lời người vận hành nhập, **Lý do trả lại** do hệ thống sinh từ số liệu.

---

## 7. Step4 — Sản xuất (Line)

### 7.1 Chọn line

Line Leader quét QR để nhận → hiện **14 line**, tick 1..n line rồi `Thêm line vào bảng`. **1 MO gộp 1 dòng**, cột `Line` hiển thị `L01, L02`, **không chia SL theo line**.

- **11B:** `Thời gian chờ` từ khi thêm line vào table đến khi bấm `Đang lắp ráp`.
- **12B:** `Thời gian thực tế` vượt yêu cầu vẫn **đếm tiếp**.
- **15A:** đúng **3 trạng thái** `Chờ xử lý ⇄ Đang lắp ráp → Hoàn thành`. Đây là trạng thái **của line** (enum `run_status` = `WAIT / RUN / DONE`), nên cột hiển thị tên là `Hiện trạng Line`.

Line chỉ chọn được khi vòng hiện tại chưa có line đó. Line của vòng trước không chặn vòng sau.

### 7.2 Bảng đang chạy — 1 MO 1 dòng

| MO  | Tên con hàng | Số lượng | Line | TG yêu cầu | TG chờ | TG thực tế | Hiện trạng Line | Kết quả thời gian | Sản lượng |
| --- | ------------ | -------- | ---- | ---------- | ------ | ---------- | --------------- | ----------------- | --------- |

- `TG yêu cầu` = hạn mức **của vòng** (§7.3), kèm chú thích `vòng 2 · 1.000/10.000`.
- `Sản lượng` chỉ có sau khi **chốt sổ Sản xuất** (§7.5) và chỉ **một dòng**: `Đạt 9.000/10.000` (vàng) hoặc `Đạt 10.000` (xanh).
  - **Không gọi phần chênh là "Thiếu".** Từ _thiếu_ đã có nghĩa riêng ở §7.5 — SL không làm ra được. Phần chênh `mục tiêu − đạt` gồm **cả hỏng lẫn thiếu**. Gọi trùng tên thì bảng báo `Thiếu 1.000` trong khi người vận hành vừa khai `thiếu 500`, đọc vào tưởng hệ thống tính sai.
  - **Không tách hỏng/thiếu ngay trong bảng.** Đây là bảng **treo tường**, liếc để biết đơn nào chưa đủ. Hỏng bao nhiêu · thiếu bao nhiêu · vì sao là câu hỏi thứ hai — bấm vào MO xem bảng `Các vòng` (§6b.4), giờ trả lời được ở **mọi thời điểm** kể cả khi vòng chưa đóng sổ.
- `TG chờ` chạy khi `Chờ xử lý`, dừng khi sang `Đang lắp ráp`.
- `TG thực tế` = **tổng các đoạn `Đang lắp ráp`**. Bấm `Dừng` thì đồng hồ này đứng, `TG chờ` chạy tiếp.
- Thời lượng hiển thị dạng `X giờ Y phút Z giây`. Header căn lề khớp với ô dữ liệu.

### 7.2b Sản lượng theo giờ — theo MO

- Panel trong Step4, **chỉ hiện form khi có MO `Đang lắp ráp`**.
- Form: `MO | Khung giờ | Số người | Sản lượng yêu cầu | Sản lượng thực tế | Ghi chú` + nút `Ghi`.

**Ba số mỗi khung giờ, cả ba đều bắt buộc:**

| Trường                | Là gì                                       | Để làm gì                                   |
| --------------------- | ------------------------------------------- | ------------------------------------------- |
| `Số người`            | số người đứng chuyền **trong khung giờ đó** | mẫu số của **Năng suất**                    |
| `Sản lượng yêu cầu`   | định mức đặt ra cho khung giờ đó            | mẫu số của **Đạt %**                        |
| `Sản lượng thực tế`   | làm ra được bao nhiêu                       | cộng dồn, đối soát với `SX đạt` của vòng    |

> **Vì sao phải đủ ba.** Một mình con số làm ra được không trả lời được câu duy nhất người quản lý cần
> hỏi: _giờ vừa rồi chạy tốt hay không_. 500 cái với 8 người là khá; 500 cái với 20 người là có vấn đề.
> Định mức 400 thì 500 là vượt; định mức 700 thì 500 là hụt. Ghi mỗi con số thực tế thì cuối ca nhìn lại
> chỉ thấy một cột số trơ, không lần ra được giờ nào hụt và hụt vì đâu.

**Hai số hệ thống TỰ TÍNH — không có ô nhập:**

```
Đạt %     = Sản lượng thực tế / Sản lượng yêu cầu
Năng suất = Sản lượng thực tế / Số người            (cái/người)
```

> Hai số này suy ra được từ ba số trên, nên cho nhập tay là mở đường cho số liệu tự mâu thuẫn — và
> người ta sẽ điền số đẹp chứ không điền số thật.

- **Đủ 24 khung giờ**, xếp vòng từ `06:00-07:00`, tự chọn đúng khung theo giờ xưởng.
- **Chặn trùng theo `ngày + khung giờ`** — MO chạy qua đêm vẫn ghi được cùng khung của ngày hôm sau.
- **Chặn vượt:** tổng **sản lượng thực tế** không vượt mục tiêu SL của vòng.
  - Vượt `Sản lượng yêu cầu` của một khung thì **không chặn** — `Đạt 117%` là tin tốt, không phải lỗi.
    Chỉ mục tiêu của cả vòng mới là trần cứng.
- Lưu `hourly[] = {moId, round, moCode, day, slot, people, target, qty, note, at, by}`, append-only.
  - Bản ghi có từ trước v2.21 không có `people` / `target` → để **null**, bảng hiện `—`.
    Không suy ngược một con số vào đó: đấy là bịa ra năng suất chưa ai đo.
- **Xem lại:** trong truy cứu MO, bấm vào dòng `4 · Sản xuất` của vòng nào thì hiện sản lượng giờ của **chính vòng đó** kèm dòng đối soát (§9).

**Đối soát với `SX đạt` của chính vòng đó — 3 trường hợp:**

| Tình huống           | Ý nghĩa                                             |
| -------------------- | --------------------------------------------------- |
| Σ giờ **=** SX đạt   | Khớp                                                |
| Σ giờ **<** SX đạt   | Ghi sót giờ — **bình thường**, chỉ ghi chú          |
| Σ giờ **>** SX đạt   | **Bất thường** — ghi trùng, hoặc khai thiếu. Báo đỏ |

> **So với `SX đạt` chứ không phải SL đã đóng thùng của cả MO.** Sản lượng giờ ghi theo vòng, nên phải so
> với con số của vòng đó; so với tổng cả đơn là lệch ngay khi MO chạy sang vòng hai.

> Sản lượng giờ hiện **không tác động** đến `TG thực tế`, `Hiện trạng Line`, `Kết quả thời gian` — chỉ để ghi nhận và đối soát. Xem §10 mục 29.

### 7.3 KPI — so THỜI GIAN, hạn mức theo vòng

```
TG yêu cầu của vòng = requiredProductionTime × SL vòng / SL MO

Kết quả thời gian = TG thực tế ≤ TG yêu cầu của vòng  →  Đạt
                  = TG thực tế >  TG yêu cầu của vòng  →  Quá giờ (kèm số trễ)

Sản lượng = chưa chốt SX            →  Chưa xong SX
          = SL đạt ≥ mục tiêu vòng  →  Đạt 10.000
          = SL đạt <  mục tiêu vòng  →  Đạt 9.000/10.000   (xem §7.2)
```

- Mốc `SL vòng` **đóng dấu vào run lúc thêm line**, nên MO đã xong vẫn giữ đúng hạn mức của vòng đó.
- **Hai cột tách riêng** vì trả lời hai câu khác nhau: _"có kịp giờ không"_ và _"có đủ hàng không"_.
- `Kết quả thời gian` **chạy live** suốt quá trình.
- **22A:** `Thời gian chờ` KHÔNG tính vào kết quả.

> Ví dụ: MO 10.000 yêu cầu 3 giờ. Vòng 1 làm đủ 10.000 → hạn 180 phút. Vòng 2 chỉ còn 1.000 → hạn **18 phút**.

### 7.4 Chạy line — 14B / 16 / 17

- **Bỏ chia SL theo line.** 1 MO gộp 1 dòng.
- **14B:** 1 line chạy nhiều MO cùng lúc, không chặn.
- **16:** các line của 1 MO **hoàn thành đồng bộ**. **Chặn** khi còn line chưa vào `Đang lắp ráp`, hoặc còn line **đang dừng** — báo rõ line nào.
- **17 — Hỏng máy:** bấm `Dừng`, **bắt buộc ghi lý do**. Line về `Chờ xử lý`, không tạo Run mới **trong cùng vòng**.
  - Hiện badge đỏ **`ĐANG DỪNG L02`** kèm lý do, phân biệt với line chưa chạy lần nào.
  - Thời gian dừng **tự động không tính** vào `TG thực tế` — rơi vào `TG chờ`.
  - Dừng quá lâu → MO về **Bàn team leader** chạy vòng mới.

### 7.5 Hoàn thành Step4 — chốt SL đạt / SL hỏng

> **SL hỏng ghi ở đây, không ghi ở Đóng thùng.** Chuyền mới là chỗ phát hiện hàng lỗi. Hàng xuống tới đóng thùng là hàng đã đạt.

Bấm `Hoàn thành (đồng bộ tất cả line)` mở form:

| Ô nhập        | Bắt buộc             | Kiểm tra                                                               |
| ------------- | -------------------- | ---------------------------------------------------------------------- |
| `SL đạt`      | ≥ 0                  |                                                                        |
| `SL hỏng`     | ≥ 0                  |                                                                        |
| `SL thiếu`    | ≥ 0                  | **`SL đạt + SL hỏng + SL thiếu` = mục tiêu vòng**, và `đạt + hỏng > 0` |
| `Lý do hỏng`  | ✔ khi `SL hỏng > 0`  | không ghi thì chặn                                                     |
| `Lý do thiếu` | ✔ khi `SL thiếu > 0` | không ghi thì chặn                                                     |

> **Ba ô SL phải cộng đúng bằng mục tiêu vòng — đây là chốt đối soát của cả bước Sản xuất.** Mỗi PCS giao xuống chuyền phải rơi vào đúng một trong ba nhóm: _làm ra đạt_ · _làm ra nhưng hỏng_ · _không làm ra được_. Tổng lệch nghĩa là có hàng không ai khai — hệ thống **chặn, không cho chốt sổ** kèm thông báo `đang dư 200` / `đang hụt 200`.
>
> Trước đây `SL thiếu` là số hệ thống tự tính ngầm (`mục tiêu − đạt − hỏng`) nên **người khai không nhìn thấy và không ai xác nhận nó đúng**; ràng buộc cũ lại lỏng (`đạt + hỏng ≤ mục tiêu`), gõ thiếu một chữ số vẫn qua.

> **Hai lý do là hai chuyện khác nhau, phải hỏi riêng.** Hỏng 500 vì lỗi khuôn; thiếu 1.000 vì chờ bù liệu. Gộp một ô thì một trong hai mất hẳn thông tin — và **làm thiếu mà không hỏng cái nào là chuyện rất thường** (hết liệu, đổi ca, máy chậm), trước đây không có chỗ nào ghi.

Form hiện sẵn `cần X · Σ giờ Y` để đối soát, và hiện **tổng sống ngay khi gõ**: `Σ 10.000 — khớp` (xanh) hoặc `Σ 9.800/10.000 — hụt 200` (đỏ) — không bắt người vận hành bấm Xác nhận rồi mới biết mình gõ lệch.

**Mỗi vòng chỉ chốt sổ Sản xuất một lần.** Đã chốt rồi thì gọi lại bị chặn (`SX vòng 1 đã chốt sổ rồi`) — nếu không, lần chốt thứ hai sẽ ghi đè SL đã khai mà không để lại dấu vết.

Xác nhận xong:

- tất cả line `DONE` cùng một mốc, `steps[4].completedAt = now`
- lưu `sx = {qtyOk, qtyNg, qtyShort, ngReason, shortReason, at}`
- hiện ngay `đạt 8.000` · `hỏng 500 — lỗi ép nhựa` · `thiếu 1.500 — chờ bù liệu` cạnh dòng MO
- **21A:** KPI tổng MO lấy **line chạy lâu nhất**
- Step4 chỉ sang Step5 khi **cả SX và Đóng thùng đã kết thúc**

---

## 7b. Đóng thùng — chạy song song trong Step4

- Là tiến trình con của Step4, có timer riêng, hiển thị trong panel `Sản xuất`.
- **Bắt đầu:** chỉ hiện nút khi ít nhất 1 line đã `Đang lắp ráp`. Ghi `packing.startedAt`, log `PACK_START`. Không auto-close SX.
- **Kết thúc — phải sau khi Hoàn thành SX:**

| Ô nhập           | Bắt buộc | Kiểm tra                                      |
| ---------------- | -------- | --------------------------------------------- |
| `SL đã đóng thùng` | ✔        | `> 0` và **không vượt `SL đạt` của Sản xuất** |
| `Lý do`          | ✔        | luôn bắt buộc                                 |

- **Không còn ô `SL hỏng`** — đã chuyển sang bước Sản xuất.
- Mặc định bằng **SL đạt của SX**. Hiện `SX đạt X · Σ giờ Y` để đối soát.
- Log `PACK_COMPLETE` kèm SL, lý do, timer, đuôi đóng thùng, và **cảnh báo khi `SX đạt ≠ SL đóng thùng`** — lộ ra hàng đạt mà chưa đóng hết.
- **Đuôi đóng thùng:** `= packing.completedAt − steps[4].completedAt`.
  - Timer đóng thùng tổng bao trùm cả phần đuôi của SX nên không đo được năng suất đóng thùng. Ràng buộc "kết thúc sau SX" là đúng thực tế — cái sản phẩm cuối ra khỏi chuyền thì mới đóng xong được — nên giữ, và thêm **đuôi đóng thùng** để biết sau khi line dừng còn mất bao lâu.
- **Nhập kho:** MO ở lại Step4 cho đến khi có `packing.completedAt`.

### 7b.2 Đóng thùng theo giờ

- Panel song song với `Sản lượng theo giờ` (§7.2b), **chỉ hiện khi MO đang đóng thùng và đã khai `Quy cách`**.
- Form: `MO | Khung giờ | Số thùng ĐẦY | Ghi chú` + nút `Ghi`.
- Lưu `packHourly[] = {moId, round, moCode, day, slot, boxes, pcsPerBox, note, at, by}`, append-only.
- **Chặn trùng `ngày + khung giờ`** như §7.2b.
- **Chặn đóng nhiều hơn số đã làm ra:** `Σ thùng × quy cách ≤ SL đạt` (chưa chốt sổ thì so với `Σ sản lượng giờ`).

**Hai đơn vị, một chiều quy đổi:**

```
Đơn hàng đặt      →  PCS      ← mọi phép tính tiến độ chạy bằng đây
Xưởng đóng thùng    →  THÙNG    ← chỉ là cách ĐẾM cho nhanh

pcs = số thùng × quy cách   (+ phần lẻ của thùng cuối)
```

> **Tiến độ MO KHÔNG BAO GIỜ tính bằng thùng.** Mọi ràng buộc sẵn có — `đạt + hỏng + thiếu = mục tiêu vòng`
> (§7.5), cộng dồn ở Nhập kho (§8) — đều chạy bằng pcs. Đưa một đơn vị thô (bội số của quy cách) vào giữa
> dây số học đó là chỗ sinh ra lỗi, vì đơn hàng hiếm khi chia hết cho quy cách.

**Luật quyết định: THÙNG CUỐI CỦA ĐƠN ĐƯỢC ĐÓNG THIẾU.**

> `3.000 pcs ÷ 800 = 3 thùng đầy + 1 thùng lẻ 600`. Thùng lẻ dán nhãn số thật rồi nhập kho như thùng
> thường. **Đây là mặc định, không phải ngoại lệ** — đơn nào không chia hết cho quy cách cũng như vậy.
>
> Không có luật này thì đơn kẹt vĩnh viễn: đóng được 2.400, còn 600 không đủ thùng, Nhập kho thấy
> `2.400 < 3.000` nên trả về Bàn team leader; vòng sau vẫn 600 đó, vẫn 0 thùng, lặp mãi. Mà làm thêm 200 cho đủ
> 800 thì thành **sản xuất dư** khách không đặt, giao 3.200 cho đơn 3.000.

**`Hàng lẻ trên bàn` KHÔNG PHẢI `SL thiếu` — đây là chỗ hay đọc nhầm nhất:**

| | Là gì | Phải làm gì | Có mở vòng mới không |
| --- | --- | --- | --- |
| **SL thiếu** (§7.5) | **Chưa làm ra được** — hết liệu, đổi ca, máy chậm | Làm thêm | **Có** |
| **Hàng lẻ chờ đóng** | **Đã làm ra rồi**, chỉ chưa gom đủ một thùng | Không phải làm gì | **Không** |

- Trong giờ **chỉ đếm thùng ĐẦY**. Hàng chưa đủ thùng để nguyên trên bàn, giờ sau gom tiếp.
  - Vì sao không cho ghi thùng lẻ mỗi giờ: thùng lẻ chỉ đóng khi biết chắc **không còn hàng nào tới nữa**,
    tức là lúc `Kết thúc đóng thùng`, không phải giữa ca. Cho ghi lẻ từng giờ thì phép `thùng × quy cách`
    hết đúng — mà cả hệ thống dựa vào phép đó.
- Panel hiện thường trực dòng: `đã đóng N thùng = X pcs · làm ra Y pcs · lẻ trên bàn Z — chờ gom, KHÔNG phải hàng thiếu`.
- `Kết thúc đóng thùng` vẫn nhập **PCS** như cũ, nhưng hiện kèm phân rã: `3.000 pcs = 3 thùng đầy + 1 thùng lẻ 600`.

**Ba hướng khác đã cân rồi LOẠI — ghi lại để khỏi bàn lại từ đầu:**

| Hướng | Vì sao loại |
| --- | --- |
| Đổi tiêu chí đóng đơn sang `SX đạt` thay vì `SL đã đóng thùng` (§8) | Mất lớp đối soát của bước Đóng thùng. Và sai thực tế: hàng chưa vào thùng thì **chưa nhập kho được** — kho đếm thùng, không đếm hàng rời trên bàn |
| Cho tồn lẻ **mang sang vòng sau**, chờ gom đủ một thùng mới đóng | Vẫn kẹt ở **thùng cuối của đơn**: đơn 3.000 mãi mãi thiếu 200 cái cho đủ 800. Mà làm thêm 200 cho đủ là **sản xuất dư** khách không đặt — giao 3.200 cho đơn 3.000, và tốn hẳn một vòng cho đơn lẽ ra một vòng là xong |
| Làm tròn LÊN: 600 lẻ tính thành 1 thùng = 800 | **Khai khống 200 cái chưa tồn tại.** Kho nhận 3.000 mà sổ ghi 3.200 — hỏng đối soát, hỏng cả tỷ lệ phế |

> Cả ba đều là cách vá **triệu chứng**. Nguyên nhân gốc là **đơn vị**: đơn hàng đặt bằng pcs, xưởng đếm
> bằng thùng, mà đơn hàng hiếm khi chia hết cho quy cách. Hai luật ở trên xoá đúng nguyên nhân đó, nên
> **logic vòng chạy (§6b, §8) không phải sửa một dòng nào**.

---

## 8. Step5 — Nhập kho (bước cuối — giữ nút Hoàn thành)

- Hàng đợi và `Đang ở bước 5` hiển thị **SL đã đóng thùng** của vòng này để đối soát.
- Quét QR để nhận → Timer Step5 START.
- Nút `Hoàn thành` kiểm tra theo **cộng dồn**:

```
tổng = qtyDone + SL đã đóng thùng của vòng này

tổng ≥ quantity  →  COMPLETED, chốt sổ vòng cuối vào packingHistory
tổng <  quantity  →  CHƯA HOÀN THÀNH, tự động về BÀN TEAM LEADER vòng mới (§6b)
```

> **Ví dụ.** MO 10.000. Vòng 1: Sản xuất chốt **8.000 đạt + 200 hỏng**, Đóng thùng đóng **8.000**.
>
> - `tổng = 0 + 8.000 = 8.000 < 10.000` → về **Bàn team leader** · `qtyDone = 8.000` · `qtyNgTotal = 200` · `qtyRemain = 2.000`
> - UI hiện `Đã xong 8.000 — Còn 2.000` + `Trả lại lần 1` + `Về Bàn team leader — làm tiếp 2.000`
> - Line Leader quét MO ở trạm Sản xuất là chạy tiếp ngay, **không qua Kho / Setup / QC**
> - Vòng 2 chỉ cho làm tối đa **2.000**. Đóng đủ → `tổng = 10.000` → **COMPLETED**
>
> 200 cái hỏng nằm trong 2.000 phải làm bù, và được đếm riêng để tính tỷ lệ phế.

---

## 9. Quy tắc chung

- **25A:** History **append-only, giữ vĩnh viễn**. Mỗi action ghi `MO, round, step, action, user, timestamp, from→to, reason, metadata`.
  - Action: `MO_CREATE / MO_SUBMIT / MO_CANCEL / KHO_ACCEPT / KHO_HANDOVER / STEP_N_ACCEPT / STEP_N_AUTO_COMPLETE / QC_PASS / QC_FAIL / RUN_ADD / RUN_START / RUN_HOLD / STEP4_COMPLETE / STEP4_FINISH_ALL / PACK_START / PACK_HOURLY / PACK_COMPLETE / HOURLY_ADD / MO_PARTIAL / RETURN_BANCHO / RETURN_KHO / MO_COMPLETE`
- **Không cho nhảy step.** Mỗi lần nhận là 1 transaction: auto-complete step trước → ghi acceptedAt → update currentStep → ghi history.
- **Timer tính từ timestamp BE**, FE chỉ hiển thị.
  - `actualDuration(N) = nextStep.acceptedAt − step.acceptedAt`
  - `TG thực tế (line) = Σ các đoạn Đang lắp ráp`
  - `actual Packing = packing.completedAt − packing.startedAt`
  - `đuôi đóng thùng = packing.completedAt − steps[4].completedAt`
- **Mọi tính toán chỉ nhìn vòng hiện tại.** Line, KPI, thời gian, sản lượng giờ đều lọc theo `round`.
- **Bảng Timer từng bước cộng dồn thời gian qua MỌI VÒNG**, kèm chú thích `n vòng` khi bước đó chạy
  nhiều lần. Trước đây bảng chỉ đọc vòng hiện tại, nên MO đi qua Setup hai lần mà vòng cuối bắt đầu từ
  Bàn team leader thì cột Setup hiện `—` — nhìn vào tưởng chưa từng setup. Muốn tách từng vòng thì mở truy cứu MO.
- **Bảng Timer từng bước tách hai cột kết quả**, không gộp:
  - `Tiến độ SL` — `Đủ 10.000` hoặc `Còn 7 · 9.993/10.000`. Đủ hàng mà chưa `COMPLETED` thì ghi rõ _chờ bấm Hoàn thành ở Nhập kho_
  - `KPI thời gian` — `Đạt` hoặc `Quá giờ`, kèm cột `Trễ`
  - Gộp chung thì chữ `Đạt` bị đọc thành "xong đơn rồi" trong khi MO còn thiếu hàng; ngược lại khi thiếu hàng thì mất luôn kết quả thời gian.
- **Truy cứu theo MO** — bấm vào một MO ở tab Lịch sử & KPI:
  1. **Các vòng** — mỗi vòng 1 dòng, **kể cả vòng đang chạy** (badge `đang chạy`): bắt đầu từ đâu · 4 cột số (SX đạt · SL hỏng · SL thiếu · đã đóng thùng) · 3 cột chữ (lý do hỏng · lý do thiếu · ghi chú đóng thùng) · lý do trả lại
  2. **Đi qua các bước — MỖI VÒNG MỘT BẢNG**, không chỉ vòng đang chạy: ai nhận bước nào lúc mấy giờ,
     mất bao lâu, và **ai làm bước trước đóng lại**. Vòng cũ trước đây coi như mất dấu
  3. **Bấm vào dòng `4 · Sản xuất`** của một vòng thì bung ra hai bảng của **chính vòng đó**:
     - **Năng suất từng line** — TG chờ · TG thực tế · hạn mức vòng · kết quả thời gian · trạng thái,
       kèm lý do dừng nếu line từng hỏng máy
     - **Sản lượng theo giờ** — từng khung giờ: số người · SL yêu cầu · SL thực tế · Đạt % · năng suất,
       dòng tổng cộng cả yêu cầu lẫn thực tế và đối soát với `SX đạt` của vòng
     Chỉ bung khi bấm: để mở sẵn thì bảng dài gấp đôi, mà phần lớn lúc người ta chỉ liếc giờ giấc các bước
  4. **Nhật ký đầy đủ** — toàn bộ bản ghi của MO đó

---

## 9b. Phân quyền — ai thấy gì, ai bấm được gì

> **Chốt ngày 2026-09-14**, thay cho câu hỏi mở #26.

### 9b.1 Sáu phòng ban, mỗi phòng một step

| # | Phòng ban | Step phụ trách | Ở đâu |
|---|---|---|---|
| 0 | **Kho xuất** | Bàn giao xuống xưởng | **Kho vật tư / bán thành phẩm** |
| 1 | **Setup** | Setup máy | xưởng |
| 2 | **QC** | Kiểm | xưởng |
| 3 | **Bàn team leader** | Chờ vào chuyền | xưởng |
| 4 | **Sản xuất** | Chạy chuyền · chốt sổ · **và Đóng thùng** | xưởng |
| 5 | **Kho nhập** | Nhận hàng về kho | **Kho thành phẩm** |

### HAI KHO, không phải hai thao tác của một kho

Đây là chỗ dễ nhầm nhất của cả tài liệu, nên nói thẳng:

> **Kho xuất (step 0) và Kho nhập (step 5) là HAI KHO VẬT LÝ KHÁC NHAU** — hai toà
> nhà, hai tổ người, hai người quản lý. Không phải một kho làm hai việc.

| | Kho xuất · step 0 | Kho nhập · step 5 |
|---|---|---|
| Chứa gì | vật tư, bán thành phẩm | **thành phẩm** đã đóng thùng |
| Hàng đi hướng nào | **ra** khỏi kho, xuống xưởng | **vào** kho, từ xưởng lên |
| Việc làm | bàn giao (§3) | nhận và đếm lại (§8) |
| Sổ trong DB | `warehouse_out` | `warehouse_in` |

Gộp chung một vai thì người giao vật tư **tự nhận luôn thành phẩm của chính lô
mình giao** — mất hẳn lớp đối soát giữa đầu vào và đầu ra. Đó là lý do tách, không
phải vì thích chia nhỏ.

Một người **vẫn kiêm được hai kho** nếu xưởng nhỏ — gán hai vai. Nhưng đó phải là
quyết định có chủ ý, không phải hệ quả của việc hệ thống không phân biệt nổi.

**Đóng thùng thuộc phòng Sản xuất**, không phải phòng thứ bảy. Nó chạy song song bên
trong Step 4 chứ không phải một step riêng (§7b), nên quyền của nó đi theo Sản xuất.

### 9b.2 Trong mỗi phòng: Leader và Member

Mỗi phòng ban có hai cấp: **Leader** và **Member**.

**Hiện tại hai cấp có quyền Y HỆT NHAU.** Vẫn tách ra ngay từ đầu vì sau này chắc
chắn phải siết (ví dụ: chỉ Leader được chốt sổ, chỉ Leader được huỷ thao tác đã
nhận). Tách sau thì phải sửa dữ liệu của mọi tài khoản đang chạy; tách sẵn thì chỉ
đổi một dòng kiểm tra.

### 9b.3 Ba mức quyền

| Mức | Nghĩa |
|---|---|
| **View** | Xem được dữ liệu của step đó |
| **Accept** | Quét nhận MO tại step đó |
| **Edit** | Nhập / sửa số liệu của step đó |

**Full** = có cả ba.

### 9b.4 Ma trận quyền

| Phòng ban | Step của mình | Step 4 · Sản xuất **+ Đóng thùng** | Step khác |
|---|---|---|---|
| Kho xuất (0) | **Full** | View | — |
| Setup (1) | **Full** | View | — |
| QC (2) | **Full** | View | — |
| **Bàn team leader (3)** | **Full** | **FULL** ← ngoại lệ | — |
| Sản xuất (4) | **Full** | *(chính nó)* | — |
| Kho nhập (5) | **Full** | View | — |
| **PLANNER** | **Full mọi step** | **Full** | **Full** |

> **Đóng thùng KHÔNG phải một step riêng — nó nằm trong Step 4.** Đóng thùng thuộc
> phòng Sản xuất (§7b), chạy song song với chuyền. Nên cột "Step 4" ở trên phủ cả
> hai sổ: `production` và `packing`. Quyền ghi trên step 4 là ghi được cả hai; quyền
> xem trên step 4 là xem được cả hai.

Ba điều cần nhớ:

**1. Ai cũng xem được Step 4 — kể cả Đóng thùng.** Sản xuất là chỗ quyết định tiến độ,
nên mọi phòng ban đều cần biết MO đang chạy chuyền nào, đạt bao nhiêu, sản lượng
từng giờ, **và đã đóng thùng được bao nhiêu**. Nhưng chỉ **xem**, không bấm được gì.

Đóng thùng là số cuối cùng trước khi hàng về kho, nên Kho nhập cần thấy để biết sắp
nhận bao nhiêu; QC và Setup cần thấy để biết lô mình làm đã ra thành phẩm chưa.
Giấu bớt thì cả xưởng phải gọi điện hỏi nhau.

**2. Bàn team leader là ngoại lệ DUY NHẤT — có full quyền trên Step 4**, kể cả Đóng thùng.
Nghĩa là người ở Bàn team leader gán chuyền, cho chạy, bấm dừng, chốt sổ SX và đóng thùng
được, y như người Sản xuất. Lý do: Bàn team leader đứng ngay trước chuyền, thực tế hai tổ
này làm việc lẫn nhau.

**3. Ngoài step của mình và Step 4, không thấy gì.** QC không mở được màn hình Kho,
Kho không mở được màn hình QC.

### 9b.5 Bảng đang chạy — ngoại lệ về phạm vi xem

`Bảng đang chạy` (§7.2) hiện MO ở **mọi step**, và **mọi phòng ban đều xem được**.

Không mâu thuẫn với 12.4: cái bị giới hạn là **màn hình thao tác của từng step**.
Bảng đang chạy là bảng tổng quan để cả xưởng biết đơn hàng đang tới đâu — giấu bớt
thì mỗi tổ mù về công đoạn trước và sau mình, gọi điện hỏi nhau nhiều hơn.

### 9b.6 PLANNER

PLANNER **full quyền mọi step của mọi phòng ban** — xem, quét nhận, nhập sửa, toàn
bộ quy trình. Đây là vai điều độ, phải vào được mọi chỗ khi có sự cố.

### 9b.7 Danh sách vai

6 phòng × 2 cấp + PLANNER = **13 vai**:

```
WAREHOUSE_OUT_LEADER   WAREHOUSE_OUT_MEMBER   ← Kho XUẤT, step 0 · kho vật tư
SETUP_LEADER           SETUP_MEMBER           ← Setup, step 1
QC_LEADER              QC_MEMBER              ← QC, step 2
WAITING_LEADER         WAITING_MEMBER         ← Bàn team leader, step 3
PRODUCTION_LEADER      PRODUCTION_MEMBER      ← Sản xuất, step 4 + Đóng thùng
WAREHOUSE_IN_LEADER    WAREHOUSE_IN_MEMBER    ← Kho NHẬP, step 5 · kho thành phẩm
PLANNER
```

Một người **giữ được nhiều vai** — tổ trưởng kiêm hai phòng thì gán hai vai.

### 9b.8 Còn chưa chốt

* Leader khác Member ở chỗ nào (hiện y hệt) — chốt khi xưởng chạy thật và thấy cần.
* Có cần vai chỉ-xem cho quản lý cấp trên không (xem hết, không bấm gì).

---

---

## 10. Những điểm CHƯA chốt

| #      | Câu hỏi                                                         | Ghi chú                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| ------ | --------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 4      | Khóa sửa sau Submit?                                            | **Đã chốt 4A: khóa cứng**                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| 5      | Phiếu in cần gì?                                                | **Đã chốt: đơn giản, chỉ cần MO Code để quét**                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| 10     | Timer riêng hay chung?                                          | **Đã chốt: riêng từng bước**                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| 13     | Chia SL cho line?                                               | **Đã chốt: BỎ — 1 MO 1 dòng**                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| 14     | 1 line chạy 2 MO?                                               | **Đã chốt 14B: cho chạy chung**                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| 16     | Step4 xong khi nào?                                             | **Đã chốt 16: đồng bộ, chặn nếu còn line đang dừng**                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| 17     | Hỏng máy?                                                       | **Đã chốt 17: Dừng + lý do → `Chờ xử lý` + badge đỏ**                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| 20     | KPI chấm theo gì?                                               | **Đã chốt: so THỜI GIAN, hạn mức theo vòng, 2 cột**                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| 21     | KPI tổng MO nhiều line?                                         | **Đã chốt 21A: line chạy lâu nhất**                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| 24     | Pause/Resume?                                                   | **Đã chốt: gộp vào 17, chỉ 3 trạng thái**                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| 27     | Vòng mới do thiếu SL có cần QC lại?                             | **Đã chốt: KHÔNG — về thẳng Bàn team leader**                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| 34     | SL hỏng ghi ở bước nào?                                         | **Đã chốt: ở Sản xuất, không ở Đóng thùng**                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| 35     | Nhận bằng quét hay bấm?                                         | **Đã chốt: quét ở mọi bước, bỏ nút Accept trên từng dòng**                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| 26     | Phân quyền chi tiết?                                            | **Đã chốt 2026-09-14 — xem §9b.** 6 phòng ban (Kho và Nhập kho tách riêng), mỗi phòng Leader + Member quyền y hệt, ai cũng View được Step 4 (gồm cả Đóng thùng), Bàn team leader có Full trên Step 4, PLANNER full mọi step
| 28     | Giới hạn số vòng trả lại?                                       | **Mở** — hiện không giới hạn                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| 29     | Chống lách KPI thời gian                                        | **Mở** — `Hoàn thành SX` bấm sớm → Đạt, rồi đóng thùng thong thả. Hướng: cảnh báo khi đuôi đóng thùng quá dài, hoặc chặn bằng `Σ sản lượng giờ`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| 30     | Thời gian tổng của MO                                           | **Mở** — `steps` reset mỗi vòng nên không có `leadTimeTotal`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| 31     | Ngưỡng dừng máy                                                 | **Mở** — "dừng quá lâu → về Bàn team leader" chưa có ngưỡng, chưa có nút. **Hệ quả hiển thị:** nếu sau này làm `Hiện trạng MO` (#39) thì chặng _mọi line đều dừng_ cần ngưỡng này để quyết định báo vàng hay báo đỏ — đỏ ngay từ phút đầu thì đổi ca, giải lao, chờ liệu đều làm bảng đỏ, riết rồi không ai nhìn                                                                                                                                                                                                                                                                                                                                |
| 32     | Nhận đồng thời & đường lùi                                      | **Mở** — chưa kiểm "MO đã có người nhận chưa"; chưa có REVERT                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| 33     | Lịch ca làm việc                                                | **Mở** — timer chạy 24/7                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| **36** | **Số chạy của mã MO do ai cấp?**                                | **Mở** — hệ thống tự tăng, hay lấy từ ERP? Ảnh hưởng tới việc có giữ chức năng tạo hàng loạt hay không (§2.2)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| **38** | **Bước Đóng thùng có cần ô nhập SL không?**                       | **Mở** — vì hàng tới đóng thùng luôn là hàng đạt nên `SL đã đóng thùng` gần như luôn bằng `SX đạt`. Hai số chỉ khác khi **đóng thùng chưa đóng hết hàng đạt** (hết thùng, hết ca). Không có tình huống đó thì bỏ ô nhập, để hệ thống tự lấy bằng `SX đạt`.<br><br>**v2.22 làm câu này gần chốt hơn nhưng CHƯA chốt (§7b.2).** Vì thùng cuối được đóng thiếu, phần lẻ luôn vào được thùng lẻ, nên cuối vòng hai số bằng nhau — tức là ô nhập gần như thừa. Chỉ còn đúng một tình huống giữ nó lại: **hết ca, hàng đạt còn nằm trên bàn chưa đóng**, lúc đó `SL đã đóng thùng` thật sự nhỏ hơn `SX đạt` và phần chênh là hàng phải làm tiếp ở vòng sau. Hỏi xưởng xem tình huống này có thật không rồi mới quyết                                                                                                                                                                                                                                                                                                                                                                                     |
| **39** | **Có cần thêm cột `Hiện trạng MO` bên cạnh `Hiện trạng Line`?** | **Mở — đã bàn 2026-09-12, tạm hoãn.** Cột hiện tại chỉ suy từ trạng thái line nên trong cửa sổ _"đã chốt sổ SX → chưa nhập kho"_ nó báo `Hoàn thành` màu xanh trong khi MO còn đóng thùng, còn nhập kho, và có thể còn thiếu hàng. Phương án đã phác: 5 chặng của MO — `Chờ chạy` · `Chờ chạy bù N` (vòng ≥2 do thiếu SL) hoặc `Chờ chạy lại — rework` (vòng mới do QC FAIL) · `Đang sản xuất` · `Chờ kết thúc đóng thùng` · `Chờ Nhập kho quét`; chữ `Hoàn thành` không xuất hiện trong bảng đang chạy vì nó chỉ đúng khi `status = COMPLETED`, mà lúc đó MO đã rời Step4. Trạng thái **suy ra hết từ dữ liệu đang có**, không thêm cột DB |
| **40** | **Bỏ in ở Kho thì mã QR dán lên hàng đến từ đâu?** | **Mở** — tem do ERP hoặc bộ phận khác in sẵn thì xong; nếu không thì vẫn phải có một chỗ in phiếu, chỉ là không nằm ở bước Kho nữa. Chưa trả lời được câu này thì quy trình quét ở 6 trạm còn một mắt xích chưa rõ |
| **37** | **Ký tự trước mã khi quét có mang ý nghĩa?**                    | **Mở** — nếu sau này dán QR cho **line** hoặc **thẻ nhân viên** thì ký tự đó chính là cách phân biệt loại nhãn, lúc đó phải giữ chứ không vứt                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |

---

## 11. MVP

**Phase 1 (đủ để demo):** Tạo lẻ + hàng loạt → Submit loạt → Kho bàn giao → **quét QR ở cả 6 trạm** → Step4 chọn line + 3 trạng thái + chốt SL đạt/hỏng + Đóng thùng song song + Sản lượng theo giờ → Nhập kho → vòng lặp về Bàn team leader → History + truy cứu theo MO.

**Phase 2:** ~~Phân quyền (#26 — đã chốt, §9b)~~ · chống lách KPI (#29) · lead time tổng (#30) · ngưỡng dừng máy (#31) · nhận idempotent + REVERT (#32).

**Phase 3:** Dashboard · yield & tỷ lệ phế theo lý do hỏng · bottleneck · downtime theo lý do · lịch ca (#33) · export Excel/PDF.

---
_v2.20 — thêm §9b Phân quyền (chốt #26). Đồng bộ với `demo/mes-v2-console.html` Version 47.
Các mục **Mở** còn lại ở §10 chờ chốt đợt 2._
