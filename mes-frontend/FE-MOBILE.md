# FE-MOBILE — responsive cho điện thoại

> Đọc cùng: `FE-PLAN.md` (luật chung) · `FE-REBUILD.md` §9 (trạm suy từ vai, người vận
> hành cầm **điện thoại của mình** đi theo hàng).
>
> File này chép lại *vì sao* các lựa chọn responsive lại như vậy. Code không có chú
> thích cho mấy chỗ này — lý lẽ nằm ở đây.

---

## 1. Ngưỡng nào chia máy tính với điện thoại

**`lg` (1024px) là ranh giới "có thanh bên hay không".** Dưới ngưỡng đó thanh bên
thành ngăn kéo trượt; từ ngưỡng đó trở lên nó đứng cố định như cũ.

`sm` (640px) dùng cho việc nhỏ hơn: giãn cách, cỡ chữ tiêu đề, số cột của lưới thẻ.

Không dùng `md` (768px) làm ranh giới chính. Máy tính bảng dựng ngang ở trạm rộng
1024–1280px — để ranh giới ở 768 thì đúng loại máy mà FE-PLAN §1 nhắm tới lại rơi
vào bố cục điện thoại.

## 2. Thanh bên → ngăn kéo

`StationSidebar` nhận `open` / `onClose`. Dưới `lg` nó là `fixed` + `-translate-x-full`,
có lớp phủ mờ bấm để đóng; từ `lg` là `static` và `translate-x-0` nên desktop không
đổi một pixel nào.

Ngăn kéo **tự đóng khi đổi trang** — nghe `usePathname` + `useSearchParams`. Không có
cái này thì bấm một mục xong ngăn kéo vẫn che nguyên màn hình vừa mở.

Nút mở nằm ở `AppTopbar` (`lg:hidden`). Breadcrumb trên điện thoại chỉ hiện **mảnh
cuối** — mảnh đầu là tên trạm, đã có ở tiêu đề trang ngay bên dưới.

## 2b. Ai cuộn: trình duyệt hay `main`?

**Dưới `lg` là TRANG cuộn, không phải `main` cuộn.** Khung `h-dvh` + `overflow-hidden`
+ `main` cuộn bên trong chỉ đúng trên desktop. Trên điện thoại nó hỏng theo hai cách
người dùng nhìn thấy ngay:

- Thanh địa chỉ của trình duyệt thu vào / nhả ra làm vùng nhìn thấy đổi chiều cao,
  trong khi khung đã khoá cứng — **cuộn tới đáy vẫn còn nội dung bên dưới**.
- Thanh bên `fixed inset-y-0` neo theo *layout viewport* (luôn là bản CAO), nên đáy
  ngăn kéo — chỗ để nút **Đổi người** — chui xuống dưới thanh địa chỉ.

Nên: gốc là `min-h-dvh` (chỉ `lg:h-dvh lg:overflow-hidden`), `main` **không** đặt
`overflow` dưới `lg`, `AppTopbar` là `sticky top-0` (`lg:static`), và thanh bên dùng
`top-0 h-dvh` thay cho `inset-y-0`.

Không đặt `overflow-x-hidden` lên `main` ở mobile: theo CSS, một trục `hidden` đi với
trục kia `visible` thì trục `visible` **tự thành `auto`** — `main` lại biến thành khung
cuộn, đúng thứ vừa bỏ. Chặn tràn ngang để cho từng thẻ/bảng tự lo (§4, §4b); đã đo
`scrollWidth == clientWidth` trên mọi màn.

Ngăn kéo mở thì khoá `document.body.style.overflow` — không thì nền vẫn cuộn sau lớp phủ.

## 2d. Thanh bên: khung CỐ ĐỊNH, chỉ khúc giữa cuộn

`aside` là `h-dvh` + `overflow-hidden`; **`nav` giữa mới là `min-h-0 flex-1
overflow-y-auto overscroll-contain`**. Khối thương hiệu trên và khối người dùng +
nút *Đổi người* dưới đều `shrink-0`, nên luôn thấy được dù danh sách dài bao nhiêu.

Để `overflow-y-auto` lên chính `aside` là hỏng: `nav` không còn lý do co lại nên nó
cao hết nội dung, khối dưới bị đẩy khỏi màn, và cuộn thì **mất luôn khối thương
hiệu ở trên** — cả ngăn kéo trôi thay vì chỉ danh sách trôi.

`min-h-0` trên `nav` là bắt buộc: `flex-1` một mình vẫn dính `min-height: auto`
(bằng chiều cao nội dung) nên không co được. Ở đây `overflow-y-auto` đã đủ để
trình duyệt cho co, nhưng ghi rõ `min-h-0` để khỏi phụ thuộc mẹo đó.

Đo ở 473×881 với vai điều độ (danh sách dài nhất, nhóm Báo cáo mở): thương hiệu
0–69, `nav` 69–729 (`scrollHeight 823 > clientHeight 660`), khối dưới 729–881.

## 2c. `.pt-safe` / `.pb-safe` không dùng chung với `py-*` được

Hai lớp đó khai trong `globals.css` **sau** `@tailwind utilities`, cùng độ đặc hiệu
một lớp, nên chúng **thắng** `py-3` và đạp padding của cạnh đó về `env(...)` — trên
máy không có tai thỏ là về **0**. Đó là lý do thanh trên cùng trông "sát mép".

Chỗ nào cần cả hai thì viết thẳng: `pt-[calc(0.75rem+env(safe-area-inset-top))]`.
Tailwind tự chèn khoảng trắng quanh `+` trong `calc()` khi sinh CSS.

## 2e. Thu gọn thanh bên thành dải biểu tượng (desktop)

Nút hình khung-chia-đôi ở góc phải khối thương hiệu (`lg:flex`, chỗ mobile để dấu X)
thu thanh bên `w-72` xuống **dải `w-16`**: chỉ biểu tượng, không nhãn, không tiêu đề
nhóm; nút bung ra nằm ngay đầu dải. Trạng thái ở `useUiStore.navCollapsed`, có
`persist` nên giữ qua lần mở sau.

Nhóm điều hướng chính **không có biểu tượng** — nó là các bước đánh số (`1 Tổng quan`,
`2 Tạo lệnh`…). Trong dải, `RailLink` lấy `item.icon`, thiếu thì rơi về `item.index`:
con số CHÍNH LÀ ký hiệu của bước đó, và nó khớp với con số ở `StepFlow` trên trang.
Nhãn đầy đủ nằm ở `title` + `aria-label`.

Con số hàng đợi (`item.count`) vẫn hiện, thành huy hiệu nhỏ góc trên phải —
"trạm mình còn 41 lệnh" là thứ không được mất khi thu gọn.

Mục có mục con (`Báo cáo sản xuất`) trong dải là **một liên kết thẳng** tới trang báo
cáo, không phải nhánh xổ ra: dải rộng 64px không đủ chỗ cho cây hai tầng, và ba bước
con đã có sẵn ở `StepStrip` ngay trên trang.

Hai bản (đầy đủ / dải) dựng song song rồi bật tắt bằng `lg:hidden` — không đoán
breakpoint bằng JS, và khổ mobile luôn nhận bản đầy đủ vì ở đó thanh bên vốn là ngăn
kéo, thu gọn nữa là hai nút làm cùng một việc.

Chuyển động: `aside` có `transition-[transform,width] duration-200 ease-out`
(`motion-reduce:transition-none`). Ba khối của bản đầy đủ ghim `lg:w-72` và dải ghim
`lg:w-16` — **không** để chúng ăn theo bề ngang đang chạy của `aside`, không thì suốt
200ms đó chữ dồn hàng và cắt lại liên tục. Ghim rồi thì chúng chỉ bị `overflow-hidden`
xén dần, trông như trượt ra. Dải còn thêm `fade-in` vì nó mount mới mỗi lần thu gọn.

## 3. "Vừa đúng một màn" chỉ áp cho desktop

Nhiều màn ép nội dung vừa một khung nhìn rồi cho cuộn BÊN TRONG thẻ (`fill`).
Trên điện thoại cách đó vỡ: tiêu đề + gợi ý luồng + dải bước đã ăn ~350px, phần còn
lại cho bảng chỉ còn hơn 200px — cuộn trong một khung 200px tệ hơn cuộn cả trang.

Nên mọi cặp `min-h-0 flex-1` đổi thành `lg:min-h-0 lg:flex-1`. Dưới `lg` các thẻ cao
tự nhiên và **cả trang** cuộn dọc; từ `lg` hành vi một-màn giữ nguyên.

Chạm vào: `StationPage`, `ChartFrame`, `DataTable`, `AppCard` (qua `className` do
nơi gọi truyền), `QueueList`, `AtStationTable`, `RunningTable`, `Overview`, và các
trang `mos` · `reports` · `warehouse-out` · `production`.

## 4. Bảng: cuộn ngang, không bóp cột

Bảng rộng nhất có 12 cột (`RunningTable`). Không có cách nào nhét 12 cột vào 390px
mà còn đọc được, và đổi sang "mỗi dòng một thẻ" thì mất khả năng liếc dọc theo cột —
thứ khiến bảng đáng dùng.

Nên `DataTable` dưới `md` **luôn** `whitespace-nowrap`, và hộp bọc luôn có
`overflow-x-auto`. Cột giữ nguyên bề ngang, người dùng vuốt ngang trong lòng bảng.
Từ `md` trở lên thì trả lại cho tham số `nowrap` của nơi gọi quyết định như cũ.

Đệm ô cũng co lại (`px-3` thay `px-5`) để một màn thấy được nhiều cột hơn.

## 4b. Danh sách thẻ cũng cuộn ngang

`QueueList` không phải bảng mà là `ul` các dòng flex, nên nó **bóp cột** thay vì tràn:
tên con hàng còn 3 chữ rồi cắt, dòng "chờ từ lúc… · 40 giờ" xuống hai hàng.

Khung cuộn tách ra một `div` bọc ngoài, còn `ul` là `w-max min-w-full` — rộng đúng
bằng **dòng rộng nhất**, tối thiểu bằng khung. Đặt `w-max` lên từng `li` thì mỗi dòng
tự co theo nội dung của chính nó: dòng Vòng 2 (có thêm "1.200/6.000") rộng hơn dòng
Vòng 1, mép phải răng cưa và các cột không thẳng hàng. Từ `sm` trả `ul` về `w-auto`.

Ô huy hiệu vòng để `w-40` dưới `sm` để cạnh trái của "Vòng 1" và "Vòng 2" thẳng nhau —
không thì phần tỷ lệ đi kèm đẩy huy hiệu lệch mỗi dòng một chỗ.

Không đặt một con số `min-w-[Nrem]` cứng: nội dung dài ngắn tuỳ trạm (trạm 5 hiện số
thùng, trạm khác hiện pcs), chọn số nào cũng sai ở một trạm nào đó.

## 4c. Thanh "một đoạn chữ + một nút"

Chữ để `min-w-0 flex-1` cạnh `AppButton` (vốn `whitespace-nowrap`) thì trên điện thoại
nút giữ nguyên bề ngang còn chữ co về gần 0 — ra một cột chữ dọc bên trái nút.

Nên các thanh này dưới `sm` cho chữ `w-full` và nút `w-full`, tức xếp hai dòng:
thanh "Bàn giao tất cả" ở `warehouse-out`, thanh việc-tiếp-theo ở `ProductionWorkspace`,
`PickedBar` ở `/production`, dòng "In bằng trình duyệt" ở bước Xem phiếu.

## 5. Dải bước

`StepFlow` / `StepStrip` trên điện thoại xuống **hai ô một hàng** (`basis-[46%]`) thay
vì ép 3–4 ô vào một hàng. Dòng mô tả phụ (`sub`) ẩn dưới `sm`: ở bề ngang đó nó chỉ
còn vài chữ rồi cắt, chiếm chỗ mà không nói được gì.

## 6. Hộp thoại thành tấm trượt đáy

`AppModal` dưới `sm` chiếm hết bề ngang, bo góc trên `20px`, cao tối đa **`50dvh`**,
chân hộp chừa `env(safe-area-inset-bottom)`. Từ `sm` là hộp giữa màn, `max-w-xl`,
`88dvh` như cũ.

**Hộp thoại vẽ qua portal ra `document.body`.** `position: fixed` neo theo phần tử
tổ tiên gần nhất CÓ `transform`, chứ không phải theo khung nhìn. Thanh bên giờ mang
`transition-[transform,width]` + `translate-x-*` để trượt ngăn kéo, nên
`RoleSwitchModal` — vốn render bên trong `aside` — bị ép vào đúng 288px bề ngang
thanh bên và dính mép trái. Cùng lý do `useAnchoredMenu` và `Tooltip` đã portal từ trước.

Kèm theo là một thang `z-index` thống nhất, vì sau khi ra `body` thì modal và ngăn kéo
mới thật sự so bậc với nhau:

| lớp | bậc |
| --- | --- |
| thanh trên dính (`sticky`) | 30 |
| lớp phủ ngăn kéo | 40 |
| thanh bên / ngăn kéo | 50 |
| hộp thoại | 60 |
| khung nổi (dropdown · lịch · chú giải) | 70 |
| toast | 80 |

## 6b. Máy quét camera chiếm trọn màn

`CameraScanModal` không còn là hộp thoại: nó là một mặt phẳng **`fixed inset-0`** vẽ
qua portal — hình camera `object-cover` kín màn, khối thương hiệu ở đỉnh, nút quay lại
góc trái, khung ngắm giữa màn, và dải thao tác ở đáy. Quét mã là việc chiếm trọn sự
chú ý; nhét nó vào tấm trượt cao 50% thì khung ngắm còn bằng bao diêm.

Ba chỗ phải ép `!important` vì `html5-qrcode` ghi thẳng style nội tuyến lên DOM nó
dựng: `!absolute !inset-0` cho khung chứa (thư viện đặt `position: relative` nên khung
co lại bằng chiều cao video), `[&_video]:!h-full !w-full !object-cover` cho video
(thư viện chốt `width` theo px), và `[&_#qr-shaded-region]:!hidden` để tắt lớp phủ
trắng mặc định — ta tự vẽ lớp tối và bốn góc.

Lớp tối ngoài khung ngắm là **một** `box-shadow: 0 0 0 100vmax` toả ra từ chính khung
ngắm, không phải bốn thanh che ghép lại.

Tia quét là một khối trượt bằng `top: 0% → 100%`, mang sẵn `-translate-y-full` để
**đáy** nó — vạch sáng — bám đúng mốc `top`, còn vệt mờ nằm phía trên. Quét một chiều
chứ không `alternate`: có `alternate` thì nửa chu kỳ vệt mờ đi trước vạch sáng, nhìn
ngược. Bọc trong một lớp `overflow-hidden` riêng để vệt không tràn khỏi khung, lớp đó
đặt **trong** khung ngắm nên bốn góc (`-top-1`, `-left-1`) không bị cắt.

**Camera sau phải ép bằng `exact`.** `facingMode: "environment"` trần chỉ là ràng buộc
MỀM: máy nào không khớp thì trình duyệt lặng lẽ rơi về camera trước, nên điện thoại
mở ra quét QR lại đang soi mặt người dùng. Mở theo ba nấc, dừng ở nấc đầu tiên chạy được:

| nấc | ý nghĩa |
| --- | --- |
| `{ facingMode: { exact: "environment" } }` | ép camera sau, không có thì ném `OverconstrainedError` |
| `{ facingMode: "environment" }` | ưu tiên camera sau, máy tự chọn |
| `{ facingMode: "user" }` | máy chỉ có camera trước — mở trước vẫn hơn không mở được gì |

Chỉ khi cả ba nấc hỏng mới báo lỗi quyền truy cập.

Thanh phóng to chỉ dựng khi `track.getCapabilities().zoom` có thật. Webcam máy bàn hầu
hết không có — vẽ ra một thanh trượt kéo không ăn thua còn tệ hơn là không có.

## 6c. Đừng ép CSS lên thẻ video của máy quét

`html5-qrcode` quy đổi toạ độ vùng quét bằng **hai phép chia riêng biệt**:

```js
widthRatio  = video.videoWidth  / video.clientWidth
heightRatio = video.videoHeight / video.clientHeight
drawImage(video, x*widthRatio, y*heightRatio, w*widthRatio, h*heightRatio, …)
```

Nó TIN rằng khung video cùng tỷ lệ với luồng camera, để hai tỷ lệ đó bằng nhau.

Bản toàn màn đầu tiên ép `!h-full !w-full !object-cover` lên thẻ video cho đẹp. Trên
điện thoại dựng đứng, luồng 640×480 nằm trong khung 390×844 nên hai tỷ lệ là **1,64
và 0,57** — lệch 65%. Thư viện cắt một dải ngang rồi nhồi vào khung vuông, mã QR méo
đi và **không bao giờ giải ra**. Camera lên hình, tia quét chạy, mọi thứ trông đúng —
chỉ là quét mãi không ăn, không một dòng lỗi nào.

Nên: **không đặt kích thước hay `object-fit` lên thẻ video.** Để thư viện tự dựng,
video giữ đúng tỷ lệ luồng và nằm giữa nền đen. Đo lại sau khi sửa:

| khổ màn | widthRatio | heightRatio | lệch |
| --- | --- | --- | --- |
| 390×844 | 1,641 | 1,638 | 0,2% |
| 844×390 | 0,758 | 0,758 | 0% |
| 1440×900 | 0,744 | 0,744 | 0% |

Hai thứ đi kèm, cùng mục đích "quét cho dễ ăn":

- **Bỏ `qrbox`.** Có `qrbox` là chỉ giải mã một ô giữa khung, người dùng phải ngắm
  trúng. Bỏ đi thì cả khung hình đều được giải (`canvas` bằng đúng khung video, và
  `#qr-shaded-region` không còn được dựng). Bốn góc chỉ còn là gợi ý ngắm.
- **`useBarCodeDetectorIfSupported`** — dùng bộ giải mã có sẵn của trình duyệt khi có.

Một cái bẫy nữa ở cùng chỗ: `Html5Qrcode.start()` **chỉ nhận `facingMode` hoặc
`deviceId`** ở tham số đầu và ném lỗi với mọi khoá khác. Thêm `width`/`aspectRatio`
vào đó là cả ba nấc camera đều hỏng, người dùng thấy "không mở được camera". Muốn xin
độ phân giải thì phải đi qua `config.videoConstraints`, không phải tham số đầu.

## 6d. Báo đúng LÝ DO camera không mở được

`getUserMedia` hỏng vì bốn lý do, mỗi lý do cần một hành động khác nhau của người
dùng. Gộp thành một câu "kiểm tra quyền truy cập" là bắt họ đoán — mà ba trong bốn
trường hợp thì quyền truy cập không liên quan gì:

| Lỗi | Câu báo |
| --- | --- |
| `NotAllowedError` | trình duyệt đang chặn — bấm ổ khoá cạnh thanh địa chỉ, bật Camera, tải lại |
| `NotFoundError` · `OverconstrainedError` | máy không có camera nào dùng được |
| `NotReadableError` | camera đang bị ứng dụng khác chiếm — đóng Zoom/Teams rồi mở lại |
| `SecurityError` | trang phải chạy HTTPS |

Thư viện gói lỗi gốc vào chuỗi nên phải dò tên lỗi trong câu, `e.name` không đọc được.

## 7. Biểu đồ

- `BarRow`: dưới `sm` xếp hai dòng — nhãn và con số cùng hàng, thanh trải hết bề
  ngang bên dưới. Giữ nguyên lưới ba cột từ `sm`. Làm bằng `order-*`, không nhân đôi
  markup.
- `ColumnChart`: bề ngang cột là `min(<barWidth>px, 8vw)` nên thu lại trên máy hẹp mà
  desktop vẫn đúng 56px. Sáu trạm × hai chuỗi vẫn tràn trên điện thoại — đúng ý,
  khung đã có `overflow-x-auto`.
- Ô điều khiển của `ChartFrame` xuống nguyên hàng dưới `sm` (`AppCard` cho khối
  `actions` `w-full sm:w-auto`).

## 8. Manifest

`orientation` đổi từ `landscape` sang `any`. FE-REBUILD §9 chốt người vận hành dùng
điện thoại của họ; khoá ngang là bắt họ xoay máy mỗi lần quét.

---

## Kiểm bằng mắt

Chụp ở 390×844 (điện thoại) và 1440×900 (desktop), đăng nhập bằng tài khoản dev
(`NV001` điều độ, `NV050` tổ trưởng SX, PIN `1234`):

```bash
cd mes-backend && ./run.sh dev          # cần docker compose up -d mes-db
cd mes-frontend && pnpm dev
```

Các màn đã soi: `/production` (cả ba bước), `/mos` (4 bước), `/reports` (3 bước),
`/running`, `/flow`, `/account`, `/qc` + hộp thoại kết quả, ngăn kéo điều hướng.
