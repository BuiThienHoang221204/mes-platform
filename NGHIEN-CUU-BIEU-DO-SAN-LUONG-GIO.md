# Nghiên cứu — Hiển thị "sản lượng theo giờ so với định mức"

Tài liệu tra cứu cho biểu đồ ② `Đạt định mức theo giờ` trong
[KE-HOACH-BAO-CAO-SAN-XUAT.md](KE-HOACH-BAO-CAO-SAN-XUAT.md).

Nguyên tắc tra cứu: ưu tiên **nguồn gốc** — tài liệu chính thức của nhà cung cấp,
bài của chính tác giả đề ra khái niệm, tiêu chuẩn quốc tế. Bài blog viết lại chỉ
dùng khi không có bản gốc, và được ghi rõ là nguồn thứ cấp.

**Kết luận ngắn nhất, để ở đầu cho khỏi phải đọc hết:** hour-by-hour board là một **BẢNG**,
không phải biểu đồ; mọi chuẩn đồ hoạ đều chặn ở **3–4 chuỗi** một biểu đồ; và **biểu đồ cột
nhóm nhiều lệnh là lựa chọn sai** cho màn này — không hệ thương mại nào trong sáu hệ khảo
sát làm thế. Chi tiết và nguồn ở §4.4.

| § | Nội dung |
|---|---|
| 1 | Hour-by-Hour Board — nguồn gốc, cấu trúc cột, vì sao là bảng |
| 2 | Sáu dạng chuẩn: bullet · luỹ kế · run/control chart · Pareto · OEE waterfall · heatmap |
| 3 | SAP · Ignition · Rockwell · Tulip · Grafana · Siemens dùng dạng nào |
| 4 | Ngưỡng số chuỗi, và cách hiển thị 100+ lệnh |
| 5 | Khuyến nghị cụ thể cho hệ này, theo từng nhóm người xem |
| 6 | Tóm tắt một trang |

---

## 1 · Hour-by-Hour Board — nó là BẢNG, không phải biểu đồ

### 1.1 Định nghĩa gốc

Tên chính thức trong từ điển lean của **Lean Enterprise Institute** (tổ chức do
James Womack lập, giữ bản quyền *Lean Lexicon*) không phải "hour-by-hour board" mà là
**Production Analysis Board**:

> "A display — often a large whiteboard — located beside a process to show actual
> performance compared with planned performance."
>
> — <https://www.lean.org/lexicon-terms/production-analysis-board/>

Ba điều LEI nói rõ ở cùng trang, và cả ba đều quan trọng với chúng ta:

| LEI khẳng định | Hệ quả cho thiết kế |
|---|---|
| Đặt **cạnh dây chuyền**, ngay tại chỗ làm | người đọc chính là công nhân, không phải quản lý ngồi văn phòng |
| Đây là **công cụ nhận diện và giải quyết vấn đề**, *không phải* công cụ lập lịch | cột "lý do" quan trọng ngang cột "số" |
| Tên gọi khác: production control board, progress control board, **problem-solving board** | cái tên thứ ba nói thẳng mục đích |

Nguồn: <https://www.lean.org/lexicon-terms/production-analysis-board/>

### 1.2 Cấu trúc cột thật sự

Không có một bản chuẩn duy nhất, nhưng các mô tả từ nguồn thực hành hội tụ về
cùng một bộ cột.

**Bốn cột số** (Vorne Industries, hãng làm thiết bị đo OEE, mô tả bảng truyền thống
trước khi giới thiệu sản phẩm của họ):

> bảng "tracks the required hourly target and an accumulated hourly target and
> compares these targets to the actual production and an accumulation of production
> for the entire shift"
>
> — <https://www.leanproduction.com/win-the-shift/>

Tức là: `Định mức giờ` · `Định mức cộng dồn` · `Thực tế giờ` · `Thực tế cộng dồn`.

**Cột chữ và quy trình ký nhận** (Jon Miller, Gemba Academy — bộ *101 Kaizen
Templates*, mẫu "Production Control Board"):

- Chu kỳ ghi **không nhất thiết là 1 giờ**: quy trình tốc độ cao ghi "five, ten or
  fifteen minutes", quy trình sản lượng thấp ghi "every two hours".
- Tổ trưởng ghi sản lượng của từng chu kỳ; **quản lý cấp trên ký hoặc ghi tên tắt** để
  xác nhận đã "grasped the reasons for any delays" và countermeasure đang chạy.
- Khuyến nghị dùng **bút và giấy hoặc bảng xoá được đặt ngay tại chỗ làm**, không
  vội tin học hoá.
- Một ví dụ bảng điện tử tại **Toyota Kyushu** hiển thị: mục tiêu ngày · sản lượng
  kế hoạch tính đến thời điểm hiện tại · sản lượng thực tế · **tỷ lệ thực tế trên kế hoạch**.

Nguồn: <https://blog.gembaacademy.com/2008/03/13/101_kaizen_templates_production_control_board_1/>

Gộp lại, bộ cột đầy đủ:

| Khung giờ | Định mức | Thực tế | Chênh | Định mức ∑ | Thực tế ∑ | Lý do không đạt | Đối sách | Ký |
|---|---|---|---|---|---|---|---|---|
| 07–08 | 120 | 108 | −12 | 120 | 108 | máy nén hụt hơi | gọi bảo trì | TT |

### 1.3 Vì sao lean chọn BẢNG chứ không chọn biểu đồ

Bốn lý do, rút từ chính các nguồn trên:

**① Vì cột quan trọng nhất là cột chữ.** LEI phân loại nó là *problem-solving
board*. Một biểu đồ cột không có chỗ để viết "máy nén hụt hơi". Biểu đồ trả lời
"bao nhiêu"; bảng trả lời được cả "vì sao" — mà "vì sao" mới là thứ sinh ra hành động.
(<https://www.lean.org/lexicon-terms/production-analysis-board/>)

**② Vì nó là công cụ GHI, không chỉ là công cụ XEM.** Người ta cầm bút viết lên nó
mỗi giờ. Ô trống của bảng là lời nhắc phải ghi; biểu đồ không có ô trống.
(<https://blog.gembaacademy.com/2008/03/13/101_kaizen_templates_production_control_board_1/>)

**③ Vì con số cần đọc chính xác, không cần so sánh tinh vi.** Ở khung giờ đang chạy
chỉ có một phép so: *thực tế* với *định mức* của đúng giờ đó. Đọc hai con số cạnh nhau
nhanh và chính xác hơn ước lượng chiều cao hai cột.

**④ Vì cột cộng dồn trả lời câu hỏi thật của ca.** Không phải "giờ vừa rồi thế nào"
mà "**từ đầu ca tới giờ còn kịp không**". Cột cộng dồn là thứ duy nhất trả lời được,
và nó là một con số, không phải một hình.
(<https://www.leanproduction.com/win-the-shift/>)

### 1.4 Điểm yếu của bảng giấy — do chính người bán phần mềm chỉ ra

Vorne liệt kê ba điểm yếu, và cả ba đều là thứ một MES phải bù:

1. **Cập nhật** — "If someone doesn't manually update the board, the data is
   immediately out of date".
2. **Độ chính xác của định mức** — khó đặt định mức thật khi tốc độ chạy thay đổi
   theo sản phẩm.
3. **Lịch sử** — "Once the board is cleaned… the data is gone forever!".

Nguồn: <https://www.leanproduction.com/win-the-shift/>

Điểm 3 là lý do một MES *được phép* làm thêm biểu đồ mà bảng giấy không làm được:
bảng giấy chỉ có hôm nay, MES có cả tháng.

---

## 2 · Các dạng biểu đồ chuẩn cho actual-vs-target theo giờ

### 2.1 Bullet chart — Stephen Few

Bản đặc tả gốc: **Bullet Graph Design Specification**, Stephen Few, Perceptual Edge,
bản sửa cuối 10/10/2013 —
<https://www.perceptualedge.com/articles/misc/Bullet_Graph_Design_Spec.pdf>

**Nó trả lời câu hỏi gì:** "một chỉ số đang ở đâu so với mục tiêu, và trạng thái đó
tốt hay xấu" — trong một chỗ rất hẹp.

Năm thành phần, trích nguyên văn:

> - Text label
> - A quantitative scale along a single linear axis
> - The featured measure
> - One or two comparative measures (optional)
> - From two to five ranges along the quantitative scale to declare the featured
>   measure's qualitative state (optional)

**Quy tắc bắt buộc nhớ** (đều trích từ bản đặc tả):

| Quy tắc | Nguyên văn |
|---|---|
| Vì sao có bullet chart | "developed to replace the meters and gauges that are often used on dashboards… Its linear design not only gives it a small footprint, but also supports more efficient reading than radial meters" |
| Thanh chính | "encoded as a bar… 100% black with a heavy stroke weight", dày "approximately 1/3rd the thickness of its container" |
| Mốc mục tiêu | "always be encoded as a short line that runs perpendicular to the orientation of the graph" |
| Khi thang **không** bắt đầu từ 0 | thanh phải đổi thành **ký hiệu** (dot hoặc X), không được vẽ thanh |
| Số dải nền | "limited to a maximum of five and ideally to three" |
| **Màu dải nền** | "Rather than using distinct hues, which might not be distinguishable by those who are colorblind, encode these ranges as distinct intensities from dark to light of a single hue" — ba dải: **40%, 25%, 10% đen** |

Quy tắc màu này giải quyết luôn **Bẫy D** trong kế hoạch hiện tại: Few đã bác chuyện
dùng nhiều sắc màu làm dải trạng thái, đúng vì lý do mù màu mà trình kiểm tra đã báo.

Hai chi tiết Few nói riêng, cực kỳ hợp với ca sản xuất:

- **Chỉ số càng thấp càng tốt** (phế phẩm) thì đảo thứ tự dải nền. Few nêu đích danh
  ví dụ này: "the display of defects in a manufacturing process, which we want to
  remain below some defined threshold".
- **Mục tiêu ở tương lai thì phải vẽ hình chiếu.** Few viết: so với mục tiêu tương lai
  thì "it's not always so easy to tell if you are on track to meet or surpass that
  future target"; cách chữa là tách thanh thành hai đoạn — *thực tế đến lúc này* và
  *dự phóng theo nhịp hiện tại*.

**Khi dùng:** một dòng một thực thể, cần so với mục tiêu, chỗ hẹp, nhiều dòng xếp
chồng vẫn đọc được.
**Khi KHÔNG dùng:** khi câu hỏi là *diễn biến theo thời gian*. Bullet chart cố ý bỏ
trục thời gian — nó là ảnh chụp một thời điểm.

### 2.2 Cumulative plan-vs-actual (burn-up)

**Nó trả lời câu hỏi gì:** "từ đầu ca tới giờ đang **thừa hay thiếu bao nhiêu cái**,
và khoảng cách đó đang giãn ra hay thu lại".

Đây chính là hai cột cộng dồn của bảng hour-by-hour, vẽ thành hai đường
(<https://www.leanproduction.com/win-the-shift/>). Trong lịch sử điều độ sản xuất,
kỹ thuật so luỹ kế kế hoạch với luỹ kế thực tế có tên **Line of Balance**, do Hải quân
Mỹ công bố năm 1962 — <https://projectproduction.org/glossary/line-of-balance/>

Tulip làm đúng dạng này trong app mẫu của họ: người vận hành tăng số đếm "against an
**incrementing target**" — mục tiêu tăng dần theo giờ, tức là mục tiêu luỹ kế.
Nguồn: <https://support.tulip.co/docs/mobile-hourly-production-scorecard>

**Điểm mạnh:** nhiễu từng giờ bị san phẳng; khoảng cách dọc giữa hai đường **là con
số cái thật**, đọc được bằng mắt, và vì cộng dồn tử số riêng mẫu số riêng nên không
dính bẫy "trung bình của phần trăm" (Bẫy A trong kế hoạch).
**Khi KHÔNG dùng:** khi cần tìm *đúng giờ nào* hỏng. Đường luỹ kế chỉ đi lên, một giờ
tồi chỉ làm đường hơi phẳng — rất khó thấy. Và đường luỹ kế **che mất khung giờ không
ghi sổ**: nó nối liền qua chỗ trống (Bẫy C).

### 2.3 Run chart và control chart (SPC)

**Nguyên tắc nền — Donald J. Wheeler:**

> "while some data contain signals, all data contain noise, therefore, before you can
> detect the signals you will have to filter out the noise. This act of filtration is
> the essence of all data analysis techniques."
>
> — *Separating the Signals from the Noise*, Quality Digest Daily, 3/10/2013, bản số 260
> <https://www.spcpress.com/pdf/DJW260.pdf>

Đây là câu trả lời cho "vì sao SPC phản đối phản ứng với từng điểm lẻ": một điểm dưới
mục tiêu **tự nó không mang thông tin**. Nó có thể chỉ là nhiễu thường ngày của quy
trình. Chỉ khi có giới hạn tính từ chính dữ liệu ta mới biết điểm đó là tín hiệu hay
không.

**Deming gọi việc phản ứng với nhiễu là _tampering_** và chứng minh bằng thí nghiệm
cái phễu: chỉnh phễu theo kết quả lần thả trước làm vệt sai số **rộng ra khoảng 40%**
so với để yên. Câu của Deming: "If anyone adjusts a stable process for a result that is
undesirable, or for a result that is extra good, the output that follows will be worse
than if he had left the process alone."
Nguồn: <https://deming.org/explore/the-funnel-experiment/> (trang chặn truy cập tự động,
nội dung lấy qua chỉ mục tìm kiếm) · sách của Wheeler về thí nghiệm này:
<https://www.spcpress.com/product_deming_funnel.php>

**Quy tắc đọc control chart.** Bộ gốc là bốn quy tắc Western Electric (1956), Lloyd S.
Nelson mở rộng thành tám trong *"The Shewhart Control Chart — Tests for Special Causes"*,
**Journal of Quality Technology**, 16(4), 1984, tr. 237–239 —
<https://en.wikipedia.org/wiki/Nelson_rules> (nguồn thứ cấp, nhưng ghi rõ xuất xứ bài gốc).
Quy tắc 1: một điểm cách trung bình quá 3σ. Wheeler khuyến cáo **dùng ít quy tắc thôi**;
chồng thêm quy tắc chỉ làm tăng báo động giả —
<https://www.leansixsigmadefinition.com/glossary/donald-wheeler/>

**Quy tắc đọc run chart** (không cần tính σ — hợp với xưởng hơn). Bản đánh giá định lượng
là Anhøj & Olesen, *Run Charts Revisited*, PLOS ONE 2014 (mở, bình duyệt) —
<https://journals.plos.org/plosone/article?id=10.1371%2Fjournal.pone.0113825>

| Quy tắc | Định nghĩa | Kết luận của bài |
|---|---|---|
| **Shift** | chuỗi điểm liên tiếp cùng một phía đường trung vị, dài hơn `log₂(n)+3` | báo động giả ~5%, **ổn định theo cỡ mẫu** — dùng được |
| **Crossings** | số lần đường gấp khúc cắt trung vị ít hơn ngưỡng nhị thức | báo động giả ~5% — dùng được |
| **Trend** | chuỗi tăng hoặc giảm liên tục | **kém** — chỉ bắt được ~20% trường hợp trôi tuyến tính dù có 100 điểm |

Bài cũng ghi rõ giới hạn: run chart "will not detect large and transient shifts",
và nhấn mạnh **nhìn dạng hình, không nhìn điểm lẻ**.
Bài gốc giới thiệu run chart cho giới quản lý chất lượng: Perla, Provost & Murray,
*The run chart: a simple analytical tool for learning from variation in healthcare
processes*, BMJ Quality & Safety 20:46–51, 2011 —
<https://pubmed.ncbi.nlm.nih.gov/25423037/> (bài đánh giá dẫn lại) ·
<https://www.semanticscholar.org/paper/The-run-chart:-a-simple-analytical-tool-for-from-in-Perla-Provost/9f951aacfc64c84031c23a1f9ef8deb4fe725ab4>

**Cảnh báo kỹ thuật riêng cho bài toán của ta — đây là chỗ dễ làm sai nhất.**
`Đạt %` là *tỷ lệ với mẫu số thay đổi từng giờ* (`target_qty` mỗi khung mỗi khác).
Với dữ liệu kiểu đó, giới hạn kiểm soát **không phải một cặp đường thẳng**: chúng phải
tính lại cho từng khung theo `nᵢ`, tức là hai đường răng cưa —
`UCL = p̄ + 3·√(p̄(1−p̄)/nᵢ)`. Quy ước thực hành: nếu buộc dùng một cặp giới hạn cố định
thì cỡ mẫu không được lệch quá **±25%**.
Nguồn: <https://www.spcforexcel.com/knowledge/attribute-control-charts/p-control-charts/>

**Khi dùng:** một lệnh hoặc một chuyền, xem một chuỗi giờ đủ dài (≥ 15–20 khung), người
xem đã được dạy cách đọc.
**Khi KHÔNG dùng:** trên tablet ngoài xưởng cho công nhân, khi chưa ai được huấn luyện
SPC. Một biểu đồ có đường răng cưa và quy tắc "8 điểm cùng phía" mà không ai đọc được
thì tệ hơn là không có.

### 2.4 Pareto cho lý do dừng máy

Nguồn gốc: Joseph M. Juran là người đặt tên "Pareto principle" cho quy luật *vital few
and trivial many*, và chính ông thừa nhận đã đặt nhầm tên trong bài **"The Non-Pareto
Principle; Mea Culpa"** (*Quality Progress*, 1975) —
<https://www.juran.com/wp-content/uploads/2021/03/The-Non-Pareto-Principle-1974.pdf>

Trong bài, Juran kể ông dựng mục "Maldistribution of Quality Losses" — liệt kê các
trường hợp tổn thất chất lượng phân bố lệch — và vẽ đường Lorenz cho nó. Về sau ông đổi
"trivial many" thành "**useful many**" (cùng nguồn).

**Nó trả lời câu hỏi gì:** "trong tất cả lý do làm mất sản lượng, **hai ba lý do nào**
chiếm phần lớn tổn thất — để đi sửa cái đó trước".

**Khi dùng:** tổng kết ca, tuần, tháng — cho tổ trưởng và điều độ.
**Khi KHÔNG dùng:**
- khi **chưa có mã lý do có cấu trúc**. Pareto trên ô ghi chú tự do là không thể — xem §5.5.
- theo thời gian thực. Pareto là nhìn lại, không phải để cứu ca đang chạy.
- khi tổn thất chia đều — lúc đó Pareto không chỉ ra được gì và gây ảo giác ưu tiên.

### 2.5 OEE waterfall / time-loss waterfall

**Nó trả lời câu hỏi gì:** "thời gian bỏ ra đã bốc hơi ở những nấc nào" — từ tổng thời
gian thiết bị xuống tới thời gian thật sự tạo ra hàng tốt.

Chuỗi nấc, theo tài liệu học của Factbird (hãng thiết bị đo OEE):

`Total Equipment Time` → (trừ giờ không có người) → `Manned Time` → (trừ họp, đào tạo,
bảo trì kế hoạch) → `Production Time` → (trừ đổi mã, tiếp liệu, vệ sinh) →
`Operating Time` → (trừ hỏng máy, lỗi quy trình, chờ) → `Valued Operating Time`

Bốn chỉ số rơi ra ở bốn nấc: OEE1, OEE2, OEE3, TCU.
Nguồn: <https://www.factbird.com/academy-lessons/factbirds-oee-waterfall>

Khung tổn thất phía sau là **Six Big Losses**, do **Seiichi Nakajima** đề ra năm 1971
tại Japan Institute of Plant Maintenance cùng với TPM: Equipment Failure · Setup and
Adjustments · Idling and Minor Stops · Reduced Speed · Process Defects · Reduced Yield.
Nguồn: <https://www.vorne.com/learn/tools/six-big-losses/> · <https://www.oee.com/oee-six-big-losses/>

Định nghĩa **chuẩn quốc tế** của các KPI này (kể cả OEE và các trạng thái thời gian)
nằm ở **ISO 22400-2:2014** — <https://www.iso.org/standard/54497.html>

**Khi KHÔNG dùng:** khi **không đo thời gian dừng máy**. Waterfall ăn dữ liệu thời gian,
không ăn dữ liệu sản lượng. Hệ chỉ ghi `sản lượng theo giờ` thì không dựng được waterfall
thật — chỉ dựng được một cái trông giống nó và sai.

### 2.6 Heatmap ca × giờ

**Nó trả lời câu hỏi gì:** "có **khuôn mẫu lặp lại** theo giờ trong ngày hay theo ca
không" — ví dụ giờ đầu ca luôn thấp, giờ sau nghỉ trưa luôn thấp.

**Khi dùng:** khi số thực thể (ngày, ca, lệnh) lớn tới mức không vẽ nổi đường, và câu
hỏi là *ở đâu*, không phải *bao nhiêu*.
**Khi KHÔNG dùng:** khi cần đọc giá trị chính xác. Mã hoá bằng màu là cách đọc giá trị
kém chính xác nhất trong thứ bậc mã hoá đồ hoạ — xem §4.1. Heatmap dùng để **khoanh
vùng rồi bấm vào xem chi tiết**, không dùng để báo cáo số.

---

## 3 · Các hệ thương mại dùng dạng nào cho màn hình này

Phần này khó tìm nguồn gốc nhất: tài liệu chi tiết thường nằm sau đăng nhập. Chỗ nào không
lấy được nguồn chính thức, dưới đây ghi rõ **không tìm thấy** chứ không đoán.

### 3.1 SAP Digital Manufacturing — tài liệu rõ nhất trong sáu hệ

SAP có hẳn một plug-in tên **Line Monitor Shift Progress** (mã catalog `PL0108`), chạy trong
Line Monitor POD, Work Center POD, Operation Activity POD, Order POD và Custom POD.
<https://help.sap.com/docs/SAP_DIGITAL_MANUFACTURING/57088d83d7f24b71821704db82ba8cbd/0b748187bbc648dab73b856a4931764c.html>

Nguyên văn mô tả widget:

> **`Display Hourly Progress` = OFF** — "the plugin displays a bar graph with a single bar
> that shows the Yield Quantity for the full shift and **a black line that represents the
> Total Target**."
>
> **`Display Hourly Progress` = ON** — "the plugin displays a bar graph that has **a bar for
> each hour** that shows the Yield Quantity by Time and **a black line that represents the
> hourly Total Target**."

Ba chi tiết trùng khớp đáng kinh ngạc với bài toán của ta:

**① Định mức từng giờ KHÔNG đều nhau.** SAP viết thẳng: *"The Target for each hour is **not
always evenly distributed** across each hour of the shift"* — vì mỗi giờ chạy công đoạn khác
nhau; và *"When the Target for each hour is added together, the value is equal to the Total
Target."* Đây chính là `target_qty` thay đổi từng khung của ta, và là lý do **Bẫy A** tồn tại.

**② Con số đầu màn là DELTA LUỸ KẾ, không phải phần trăm giờ.** Các giá trị header giữ nguyên
ở cả hai chế độ: **Total Target · Remainder · Total Delta · Scrap · Actual Quantity**.

> "Total Delta … represents **how far behind or ahead the production progress is at the
> current time**. When the Total Delta value is negative, it's displayed in **red text**."
>
> — <https://help.sap.com/docs/SAP_DIGITAL_MANUFACTURING/57088d83d7f24b71821704db82ba8cbd/d61b51c4a9c9489685e6ace2aa22b61b.html>

Tài liệu còn kèm bảng minh hoạ *Current Time / Total Yield / Current Target / Delta* — tức là
**mục tiêu luỹ kế tăng dần** đúng như §2.2.

**③ Chi tiết từng giờ là ĐI SÂU, không phải bày sẵn.** *"You can select the bar for each hour
to view the Target and Delta for that hour"* — bấm vào cột mới ra số. Đúng "details on demand".

**SAP dùng bullet chart cho tiến độ lệnh.** Plug-in **Line Monitor Order Progress** (`PL0022`):

> "a **bullet chart** tracking the production progress based on the goods receipt quantity for
> the order"; hiển thị "Actual Production / Planned Production"
>
> — <https://help.sap.com/docs/SAP_DIGITAL_MANUFACTURING/57088d83d7f24b71821704db82ba8cbd/024a9cdfb37e4b9ca4e2d52051f4426c.html>

Đây là bằng chứng thương mại trực tiếp cho khuyến nghị bullet chart ở §2.1 — và cũng đúng cho
biểu đồ ① `Tiến độ theo MO` trong kế hoạch hiện tại.

**Lý do dừng nằm ở plug-in RIÊNG, không nhét vào biểu đồ giờ.** Các plug-in
*Line Monitor Top 5 Availability / Performance / Quality Losses* (`PL0028`–`PL0030`, `PL0084`)
hiện "Reason code … description, Resource that's affected, Duration"; cộng plug-in **Downtime**
để gắn mã lý do và plug-in **Untagged Events** cho sự kiện chưa gắn mã.
<https://help.sap.com/docs/SAP_DIGITAL_MANUFACTURING/57088d83d7f24b71821704db82ba8cbd/e090a9f861f24346bc378f5ef71b096d.html>
· danh mục plug-in đầy đủ:
<https://help.sap.com/docs/SAP_DIGITAL_MANUFACTURING/3dc010a4880d4c8691bae0ba30f2b57b/8674f7d538334e0ebd9e3bb113af72ee.html>

Kiến trúc POD là **lắp ghép plug-in theo vai**, mỗi perspective có "overview page (Main Page)"
và "detail page (Dashboard)" —
<https://help.sap.com/docs/SAP_DIGITAL_MANUFACTURING/97c9e9b9fac74be2a023638cd1700b46/77e08a4e8bfc4d7b96fb99fd0cf69121.html>
Đúng tinh thần "mỗi vai một màn" ở §5.1.

### 3.2 Inductive Automation Ignition — có màn theo giờ thật, dùng ĐƯỜNG

Lõi Ignition chỉ là bộ linh kiện (Perspective Chart palette: Gauge, Simple Gauge, Power Chart,
Time Series Chart, XY Chart… —
<https://www.docs.inductiveautomation.com/docs/8.1/appendix/components/perspective-components/perspective-chart-palette>).
Không có linh kiện "hourly scorecard" sẵn.

Nhưng **Ignition Launchpad OEE** của chính Inductive Automation thì có, và tài liệu công khai:
<https://launchpad.docs.ia.io/oee/> · <https://pages.inductiveautomation.com/ignition-launchpad>

**Màn `Line View`** — đây là màn "theo giờ so định mức":
<https://launchpad.docs.ia.io/oee/pages/line-view/>

- Biểu đồ đường ①: "Availability, Performance, Quality and OEE **at each hour**"
- Biểu đồ đường ②: "**Target Production, Actual Production and Rejects for each hour**"
  → **đường nhiều chuỗi theo giờ, không phải cột**
- Thêm "an **hourly bar chart** showing the most productive hours in the selected time period"
- Di chuột ra X-trace hiện giá trị tại thời điểm đó
- Trang có ảnh chụp màn hình

**Màn `Production Summary`** — đây là **bảng các giờ**:
<https://launchpad.docs.ia.io/oee/pages/production-summary/>

- Đặt interval = **Hour** thì mỗi dòng là một giờ, có cột **Hour**
- Cột: **Production · Reject · Target** counts; A/P/Q/Utilization/OEE vẽ bằng **thanh tiến độ**;
  Runtime / Downtime / Idle Time theo phút
- **Không có cột chênh và không có cột luỹ kế**

**Màn `Overview`** — thẻ từng chuyền: OEE là **thanh trượt** có tooltip A/P/Q, trạng thái
Running/Faulted/Stopped, và "**current rate and target rate** details".
<https://launchpad.docs.ia.io/oee/pages/overview/>

**Không tìm thấy** Pareto mã lý do trong tài liệu Launchpad OEE — chỉ có phần trăm/phút dừng.

### 3.3 Rockwell FactoryTalk — bảng trước, biểu đồ hai chuỗi sau; giờ là mức đi sâu

Nguồn chính: **FactoryTalk Report Expert User Guide v14.00.00** (PDF chính thức) —
<https://literature.rockwellautomation.com/idc/groups/literature/documents/um/rptexp-um001_-en-e.pdf>

- **Thứ bậc đi sâu:** Site → Area → Line → Work Cell → Month → Week → Day → Shift → **Hour**.
  Giờ là **mức đáy của drill-through**, không phải màn mặc định. (tr. 32)
- **Mẫu báo cáo `Production`** là một **lưới (bảng)**: Good Parts · Scrap Parts · Total Parts ·
  **Ideal Parts** · **Ideal %** · Scrap % · Running Time · Uptime %.
  Định mức của Rockwell là **Ideal Parts** = "The total number of parts that could have been
  produced in the Available Time if OEE was 100%", `Ideal Parts = Available Time / Ideal Cycle Time`,
  và `Ideal % = GoodParts / IdealParts`. (tr. 49–51)
- **Biểu đồ actual-vs-target của Rockwell:** "The report template bar charts: **Good Parts vs.
  Ideal Parts**" — trục X là nhóm thứ nhất (là *giờ* khi đã drill xuống giờ), series là nhóm thứ
  hai. Tức là **cột hai chuỗi: thực tế và định mức**.
- **Lý do dừng:** mẫu **Root Cause Analysis** = "a **Gantt chart** displaying work cell state
  occurrences over time … Below the Gantt chart for each line is a **table** of data showing the
  same data used in the chart" (tr. 55) — tương đương state timeline.
- **Ba phát hiện phủ định, kiểm bằng tìm toàn văn cả hai sổ tay:** từ **"Pareto" không xuất hiện
  ở đâu**, **"gauge" không xuất hiện ở đâu**, **"cumulative" / "running total" không xuất hiện
  ở đâu** trong Report Expert guide. Rockwell **không ship** phần tử luỹ kế nào.
- Sổ tay FactoryTalk Metrics chỉ nói về cấu hình —
  <https://literature.rockwellautomation.com/idc/groups/literature/documents/um/pltmt-um001_-en-e.pdf>

**Câu duy nhất của Rockwell nói thẳng về màn theo giờ có định mức**, trong product profile của
FactoryTalk VantagePoint EMI:

> "Machine operators can see machine-level information, such as a dashboard that includes
> **OEE gauges, time, fault and part analysis, OEE by hour with a target** including a
> **tabular event detail list**"
>
> — <https://literature.rockwellautomation.com/idc/groups/literature/documents/pp/ftalk-pp028_-en-p.pdf>

Chú thích hình trong cùng PDF: dashboard hiệu suất kèm "**down time causes, cycle time, and
scrap rate**". PDF này có ảnh chụp màn hình.

Khuôn mẫu Rockwell cho xưởng: **gauge OEE + "OEE theo giờ có định mức" + bảng sự kiện dừng
ở dưới**.

### 3.4 Tulip — có app theo giờ, nhưng KHÔNG công bố dạng widget

**Mobile Hourly Production Scorecard** —
<https://support.tulip.co/docs/mobile-hourly-production-scorecard>

Nguyên văn: app cho người vận hành "increment an output quantity **against an increasing
target**", so với "an **incrementing target amount based upon the target per hour goal** set";
dữ liệu "written to a **table in hour increments** (Live updates but **each row in a table
represents an hour of production**)"; và "**a single step!** Everything you need is on one step".

Tức là **mô hình dữ liệu là bảng một dòng một giờ, với mục tiêu luỹ kế tăng dần**. Nhưng trang
tài liệu **không nói** người vận hành nhìn thấy bảng, cột hay một con số to, và **không có ảnh
chụp** ở cả trang KB lẫn trang thư viện (<https://library.tulip.co/apps/hourly-production-scorecard>).
Đây là một khoảng trống thật, ghi lại cho trung thực.

**Màn có tài liệu đầy đủ là `Performance Visibility Dashboard`** — và nó **theo ngày/tuần,
không theo giờ, không có định mức**:
<https://support.tulip.co/docs/performance-visibility-dashboard-1>

1. phân bố trạng thái theo ngày trong tuần — **cột xếp chồng**
2. **Pareto lý do dừng máy** trong tuần
3. tỷ lệ uptime hôm nay — **một con số**
4. trạng thái các trạm — **bảng**
5. thời gian chạy của các trạm — donut/bar
   · A/P/Q/OEE là **bốn con số đơn**

**Bộ dạng hiển thị Tulip cho phép** (<https://support.tulip.co/docs/display-types>):
Bar, **Grouped Bar**, Stacked Bar, Line, Multiseries Line, Dot Plot, Grouped Dot Plot,
**Pareto**, Donut, Scatter, **Gauge**, Histogram, Box Plot, Multiseries Box Plot.
Đáng chú ý: **Grouped Bar có sẵn — và họ không dùng nó cho màn này.**

### 3.5 Grafana — phủ định đã kiểm chứng

- Tra chính API kho dashboard của Grafana: tìm **OEE** ra đúng **6 kết quả, đều là các bản
  của MỘT dashboard cộng đồng** (<https://grafana.com/grafana/dashboards/11816-pdma-oee-equipamento/>);
  tìm **manufacturing**, **production target**, **shift production** ra **không kết quả liên quan**.
  **Grafana Labs không ship dashboard OEE hay sản lượng theo giờ chính thức nào.**
- Dashboard cộng đồng kia gồm: 3 × **singlestat**, 1 × **bargauge** (OEE), 1 × **text**.
  **Không có định mức, không có trục giờ, không có mã lý do.**
- Nguyên thuỷ Grafana cung cấp:
  **Stat** = "one large stat value with an optional graph sparkline"
  (<https://grafana.com/docs/grafana/latest/visualizations/panels-visualizations/visualizations/>);
  **Bar gauge** = "reduces every field to a single value"
  (<https://grafana.com/docs/grafana/latest/visualizations/panels-visualizations/visualizations/bar-gauge/>);
  **State timeline** = "discrete state changes over time… **state regions**… region length
  indicates the duration"
  (<https://grafana.com/docs/grafana/latest/visualizations/panels-visualizations/visualizations/state-timeline/>).
- Hướng dẫn chính thức về loại dashboard "báo trạng thái nhanh": "They are often made of
  **stat, gauge, and bar gauge panels**. They may also have **tables with color-coding and
  gauge fields**. They usually make use of **value thresholds with color-coding**."
  <https://grafana.com/blog/grafana-dashboards-a-complete-guide-to-all-the-different-types-you-can-build/>
- **Actual-vs-target không phải panel lõi.** Thứ gần nhất trên grafana.com là **plugin đối tác**
  (không phải của Grafana Labs): **SPC Bullet** của Kenso — "a progress bar, bar gauge, or full
  **bullet chart** with qualitative background zones", có "**Target marker**" để "compare actual
  vs. goal with a secondary marker from any data field". Có phí.
  <https://grafana.com/grafana/plugins/kensobi-spcbullet-panel/>

### 3.6 Siemens Opcenter — bằng chứng yếu nhất, phải nói thẳng

Những gì xác minh được từ trang của chính Siemens:

- Opcenter Execution Process 2301 thêm trang **Line Monitoring**, mô tả duy nhất là "the main
  production dashboard of the line operator". Bài có ảnh chụp nhưng **không có một dòng nào mô tả
  widget**. <https://blogs.sw.siemens.com/opcenter/whats-new-in-opcenter-execution-process-2301/>
- Opcenter Intelligence Cloud 2310 thêm **KPI target matrices gắn với chiều thời gian** — "the
  target based on a time dimension… For example, day, week, month, **work calendar shift**,
  work calendar day" — cùng "**new KPI table widget**" và "**asset state table widget**".
  **Hạt mục tiêu mịn nhất Siemens công bố là CA/NGÀY — không có giờ.**
  <https://blogs.sw.siemens.com/opcenter/whats-new-in-opcenter-intelligence-cloud-2310/>
- Opcenter Execution Foundation OEE: chỉ liệt kê năng lực (reason trees, state transition tables,
  root-cause analysis), **không mô tả dashboard, không Pareto, không định mức giờ**.
  <https://www.siemens.com/en-us/products/opcenter/execution/foundation-oee/>
- <https://www.siemens.com/en-us/products/opcenter/manufacturing-intelligence/>

**Khoảng trống ghi rõ:** `docs.sw.siemens.com` không trả về nội dung cho truy cập không đăng
nhập, `support.sw.siemens.com` yêu cầu đăng nhập. **Không có nguồn chính thức nào của Siemens
mô tả dạng widget cho sản lượng theo giờ so định mức.** Không nên giả định là có.

### 3.7 Tổng hợp sáu hệ

| | Widget actual-vs-target | Hạt giờ | Phần tử luỹ kế | Mã lý do |
|---|---|---|---|---|
| **SAP DM** | cột từng giờ + **đường định mức đen**; **bullet chart** cho tiến độ lệnh | biểu đồ; bấm vào cột mới ra số | **Có** — Total Target / Remainder / **Total Delta**, âm thì đỏ | có, ở plug-in **riêng** |
| **Ignition Launchpad OEE** | **đường nhiều chuỗi**: Target vs Actual vs Rejects theo giờ | **cả hai** — đường theo giờ và bảng có cột Hour | không | không |
| **Rockwell Report Expert** | **lưới + cột hai chuỗi** Good Parts vs Ideal Parts | **bảng trước**, giờ là mức drill đáy | không (từ "cumulative" không có trong sổ tay) | có — **Gantt + bảng** Root Cause Analysis |
| **Rockwell VantagePoint** | "OEE by hour with a target" + gauge OEE | biểu đồ | không nêu | có — "tabular event detail list" |
| **Tulip** | mục tiêu **luỹ kế tăng dần**; dạng hiển thị **không công bố** | dữ liệu là bảng một dòng một giờ | **có** (mục tiêu tăng dần) | có, nhưng ở **dashboard khác** — **Pareto** |
| **Grafana** | không có gì chính thức; plugin đối tác **bullet chart có target marker** | — | — | State timeline là nguyên thuỷ có sẵn |

**Bốn kết luận rút ra:**

**① Khuôn mẫu áp đảo cho màn theo giờ là: một cột (hoặc một điểm) mỗi giờ cho thực tế, định
mức là ĐƯỜNG phủ lên** — không phải hai cột cạnh nhau, và **tuyệt đối không phải nhiều lệnh
cạnh nhau**.

**② Con số đầu màn là delta luỹ kế, không phải phần trăm của giờ vừa rồi.** SAP nói thẳng
điều này; Tulip dựng mô hình dữ liệu quanh mục tiêu luỹ kế.

**③ Mã lý do luôn nằm ở màn/plug-in KHÁC** — Pareto (Tulip), Gantt + bảng (Rockwell),
Top-5 Losses (SAP). Không hệ nào nhét lý do vào trong biểu đồ sản lượng giờ.

**④ Không hệ nào gộp NHIỀU LỆNH vào một biểu đồ cột nhóm.** Cần chính xác ở đây: Rockwell
*có* dùng cột hai chuỗi, nhưng hai chuỗi đó là **thực tế và định mức của CÙNG một thực thể**.
Cột nhóm mà kế hoạch hiện tại đề xuất là **ba LỆNH KHÁC NHAU** trong một nhóm — dạng đó không
có ở hệ nào trong sáu hệ, kể cả Tulip là nơi `Grouped Bar` có sẵn trong bộ widget.

---

## 4 · Khi có hàng chục tới hàng trăm lệnh chạy song song

### 4.1 Có ngưỡng số chuỗi không? Có, và nó rất thấp

Đây là phần có nguồn chuẩn rõ nhất trong cả tài liệu này.

**UK Government Analysis Function** — cơ quan thống kê chính phủ Anh, tài liệu này là
**chuẩn bắt buộc** cho mọi ấn phẩm thống kê của chính phủ Anh:

> "Aim for a maximum for four lines. Presenting more than four lines on a line chart
> can be done, but it often results in the chart becoming too cluttered."
>
> "In general, we advise a limit of **four bars per cluster**."
>
> "Always rank bars by value, unless there is a natural order, for example, age or time."
>
> — <https://analysisfunction.civilservice.gov.uk/policy-store/data-visualisation-charts/>

Bản danh mục kiểm tra khả năng tiếp cận của cùng cơ quan nhắc lại như một mục bắt buộc,
và thêm một quy tắc cho small multiples:

> "All the numerical axes in a set of small multiple charts need to have **the same scale**
> to avoid misinterpretation."
>
> — <https://analysisfunction.civilservice.gov.uk/policy-store/charts-a-checklist/>

Bài học module 8 của họ nêu đích danh hai cách chữa khi vượt bốn đường: **focus chart**
(một đường đậm, các đường còn lại xám nhạt) và **small multiples** —
<https://analysisfunction.civilservice.gov.uk/support/communicating-analysis/introduction-to-data-visualisation-e-learning/module-8-line-charts/>

**IBCS** (International Business Communication Standards) còn chặt hơn — quy tắc EX 2.4
*"Replace spaghetti charts"*:

> "Line charts with more than **three** intersecting lines tend to be confusing. Instead,
> several smaller charts with one line each could be placed next to one another
> (small multiples)…"
>
> — <https://www.ibcs.com/standards/page/3/>

**Stephen Few** giải thích vì sao con số lại là bốn, bằng cơ chế nhận thức:

> "it typically limits the number of variables that can be effectively displayed in a
> single graph to four" … "working memory can only attend to three or at most four
> chunks of information at a time"
>
> — *The Perceptual and Cognitive Limits of Multivariate Data Visualization*, Perceptual Edge, 9/2019
> <https://www.perceptualedge.com/articles/misc/Limits_of_Multivariate_Data_Vis.pdf>

**Thứ bậc mã hoá đồ hoạ — Cleveland & McGill (1984)**, bài gốc trên *Journal of the
American Statistical Association*. Xếp hạng độ chính xác khi người đọc giải mã, từ tốt
nhất xuống tệ nhất:

1. Vị trí trên cùng một thang (position along a common scale)
2. Vị trí trên các thang không thẳng hàng
3. Độ dài, hướng, góc
4. Diện tích
5. Thể tích, độ cong
6. **Đậm nhạt, độ bão hoà màu** ← cuối bảng

Quy tắc thiết kế họ rút ra: *"Graphs should employ elementary tasks as high in the
ordering as possible."*
Bản quét bài gốc:
<https://math.pku.edu.cn/teachers/xirb/Courses/biostatistics/Biostatistics2016/GraphicalPerception_Jasa1984.pdf>
(bản gốc có phí: <https://www.tandfonline.com/doi/abs/10.1080/01621459.1984.10478080>)

**Kết luận số học cho ta:** 100 lệnh × 12 khung giờ là **25–50 lần** vượt mọi ngưỡng đã
công bố. Không có nguồn nào ủng hộ.

### 4.2 Vậy họ hiển thị thế nào

Bốn dạng, xếp theo số thực thể chịu được:

**① Một chỉ số tổng + đi sâu dần.** Khuôn mẫu gốc là *Visual Information-Seeking Mantra*
của **Ben Shneiderman**, bài *"The Eyes Have It: A Task by Data Type Taxonomy for
Information Visualizations"*, IEEE Symposium on Visual Languages, 1996, tr. 336–343:

> "**Overview first, zoom and filter, then details-on-demand**"
>
> — <https://www.cs.umd.edu/~ben/papers/Shneiderman1996eyes.pdf>

Shneiderman in câu này **mười lần** trong bài, mỗi dòng là một dự án mà ông lại tự phát
hiện lại nguyên tắc đó. Cùng bài: *"Exploring information collections becomes increasingly
difficult as the volume grows."*

**② Bảng xếp hạng (sorted list / dot plot).** **Naomi Robbins**, *Dot Plots: A Useful
Alternative to Bar Charts*, Perceptual Edge 2006, vẽ **60 công ty Fortune 1000 trong MỘT
dot plot** và chồng thêm chuỗi thứ hai lên cùng hình:

> "Imagine how cluttered the bar chart would be if we tried to superpose the profit data on it."
>
> "Dot plots can be used in any situation for which bar charts are typically used. They
> are less cluttered, they make it easier to superpose additional data, and they do not
> require a zero baseline as do bar charts."
>
> — <https://www.perceptualedge.com/articles/b-eye/dot_plots.pdf>

Đây là bằng chứng gốc mạnh nhất rằng **một danh sách xếp hạng chịu được hàng chục thực thể**.
Quy tắc đi kèm bắt buộc: **sắp xếp theo giá trị** (Analysis Function, nguồn ở §4.1).

**③ Small multiples / trellis.** Khung gốc là **trellis display** của Rick Becker và
Bill Cleveland (Bell Labs, 1993–1996):

> "Trellis display is a framework for the visualization of multivariable databases"
> — các panel xếp thành hàng, cột, trang; đặc trưng chính là **multipanel conditioning**,
> kèm kỹ thuật **banking to 45°** để độ dốc đọc được.
>
> — <https://9p.io/cm/ms/departments/sia/project/trellis/wwww.html>
> (bài chính thức: Becker, Cleveland & Shyu, *JCGS* 5(2):123–155, 1996)

**Ngưỡng số panel** — IBCS Chart template 13 nói thẳng con số:

> "The number of small multiples can be up to **25 or more** (depending on the number of
> columns per chart and the font-size being used)."
>
> — <https://www.ibcs.com/resource/chart-template-13/>

**④ Sparkline trong bảng — cách duy nhất có nguồn cho hàng trăm thực thể.**
**Edward Tufte**, *Sparkline theory and practice* (trang gốc của ông, sau thành chương
sparkline trong *Beautiful Evidence*, 2006):

> "**a small intense, simple, word-sized graphic with typographic resolution**"
>
> "sparkline graphics can be **everywhere a word or number can be: embedded in a sentence,
> table, headline, map, spreadsheet, graphic**"
>
> — <https://www.edwardtufte.com/notebook/sparkline-theory-and-practice-edward-tufte/>

Con số đáng nhớ ở cùng trang: thêm sparkline vào bảng so sánh quỹ đầu tư cho ta
*"an approximate look at 5,000 more numbers"* mà bảng chỉ **to thêm 21%**; và cho việc
theo dõi vận hành, **500 sparkline trên một tờ A3** cho phép so sánh đồng thời, hoạt động
*"like sentences and paragraphs"* thay vì lật từng màn hình.

**⑤ Heatmap thực thể × giờ.** **Stephen Few**, *Multivariate Analysis Using Heatmaps*,
Perceptual Edge 2006 — <https://www.perceptualedge.com/articles/b-eye/heatmaps.pdf>

> "By examining a single row, you can see a particular employee's complete multivariate
> profile. By scanning a column, you can see the complete set of values for a particular
> variable across all" (thực thể)

Hai quy tắc màu Few nêu ở đó, cần nhớ:

- **Không dùng cầu vồng nhiều sắc** — *"we don't perceive a rainbow of hues quantitatively"*.
- Dùng thang **một sắc đậm dần**, hoặc thang **phân kỳ hai sắc với điểm giữa trung tính**
  khi dữ liệu tự nhiên chia hai phía — *đúng trường hợp trên/dưới định mức của ta*.

Few cũng nói rõ điểm yếu, bằng chính cơ chế: *"the rectangles do not vary in length or in
area to encode quantitative information, but merely serve as **placeholders for colors**"* —
<https://www.perceptualedge.com/articles/visual_business_intelligence/the_visual_perception_of_variation.pdf>
Cộng với thứ bậc Cleveland & McGill (màu xếp cuối), kết luận: **heatmap để khoanh vùng,
không để đọc số**.

### 4.3 Bảng quy đổi số lệnh → dạng biểu đồ

| Số lệnh cùng lúc | Dạng nên dùng | Nguồn ngưỡng |
|---|---|---|
| 1 | biểu đồ đường / cột đầy đủ, thực tế vs định mức | AF ≤ 4 đường |
| 2–4 | vẫn một biểu đồ, tối đa 4 đường | <https://analysisfunction.civilservice.gov.uk/policy-store/data-visualisation-charts/> |
| 5–25 | **small multiples**, chung thang dọc | <https://www.ibcs.com/resource/chart-template-13/> |
| 25–100+ | **bảng có sparkline**, sắp xếp theo mức chênh; hoặc **heatmap** lệnh × giờ | <https://www.edwardtufte.com/notebook/sparkline-theory-and-practice-edward-tufte/> · <https://www.perceptualedge.com/articles/b-eye/heatmaps.pdf> |
| bất kỳ | **một con số tổng** ở trên cùng, rồi mới đi sâu | <https://www.cs.umd.edu/~ben/papers/Shneiderman1996eyes.pdf> |

### 4.4 Cột nhóm (grouped column) — vì sao nó SAI cho việc này

Nói thẳng: **biểu đồ cột nhóm là lựa chọn sai** cho "đạt định mức theo giờ". Bốn lý do
độc lập, mỗi lý do đủ để loại.

**① Nó tối ưu cho phép so SAI.** Trong một cụm, các cột chung đáy nên so sánh dùng *vị trí
trên cùng một thang* — hạng 1, chính xác nhất. **Giữa các cụm** thì cột cùng chuỗi bị các
cột khác chen giữa, người đọc bị đẩy xuống *vị trí trên thang không thẳng hàng* / *độ dài*
— hạng 2–3, và phải nhảy mắt qua nhiễu. Nhưng câu hỏi thật của ta là **"lệnh này diễn biến
thế nào qua các giờ"** — tức là so *giữa các cụm*, đúng cái mà cột nhóm làm khó nhất.
(<https://math.pku.edu.cn/teachers/xirb/Courses/biostatistics/Biostatistics2016/GraphicalPerception_Jasa1984.pdf>)

**② Few xếp cột vào loại quan hệ khác.** Trong *Graph Selection Matrix* của ông, với quan
hệ **Time Series**, đường được chấm **"Often — to feature overall trends and patterns"**,
còn cột chỉ **"Sometimes — vertical bars only, to feature individual values"**. Cột là công
cụ của quan hệ **Ranking**, không phải của Time Series. Cột nhóm theo giờ là dùng công cụ
xếp hạng để kể một câu chuyện diễn biến.
<https://www.perceptualedge.com/articles/misc/Graph_Selection_Matrix.pdf>

**③ Có phê phán trực tiếp bằng chữ.** Naomi Robbins, về đúng dạng cột nhóm:

> "**It is hard to make comparisons across counties when there are so many bars in a group.**"
>
> "the dot plot is even more powerful when replacing clustered or stacked bar charts since
> these graph forms do not communicate quantitative information as well as simple bar charts
> or dot plots do"
>
> — <https://www.perceptualedge.com/articles/b-eye/dot_plots.pdf>

Cleveland & McGill còn nói nặng hơn về cả họ biểu đồ này: cần *"radical surgery on these
popular graphs"*, và đề xuất thay bằng **dot chart có nhóm**.

**④ Trần 3 lệnh trong kế hoạch hiện tại là dấu hiệu chẩn đoán, không phải giải pháp.**
Kế hoạch §3.1 ghi *"cột nhóm + đường mục tiêu 85%, **tối đa 3 lệnh**"*, và bản mockup đã
dựng đúng như vậy — `mockup/bao-cao-san-xuat.html` ghi trong chú thích code:
*"Mỗi MỐC THỜI GIAN một nhóm, trong nhóm mỗi LỆNH một cột. Ba lệnh thì ba cột."*
Khi phải viết "tối đa 3" vào đặc tả trong lúc hệ thống có thể chạy 100 lệnh, đó là dạng
biểu đồ đang báo rằng nó không hợp bài toán. Chuẩn IBCS gọi cách chữa cho đúng tên: thay
bằng **small multiples** (<https://www.ibcs.com/standards/page/3/>).

Đáng ghi nhận: chính bản mockup đã phải thêm **dải nền xen kẽ** để *"ranh giới nhóm nhìn
ra ngay, không phải đếm cột"*. Phải thêm một lớp trang trí chỉ để người đọc biết cột nào
thuộc nhóm nào — đó là triệu chứng của việc nhóm cột, không phải cách chữa nó.

**⑤ Không hệ thương mại nào làm thế.** §3.7④: trong sáu hệ khảo sát, dạng gộp nhiều chuỗi
duy nhất xuất hiện là **thực tế vs định mức của CÙNG một thực thể** (Rockwell: Good Parts vs
Ideal Parts). **Không hệ nào gộp nhiều lệnh khác nhau vào một nhóm cột** — kể cả Tulip, nơi
`Grouped Bar` có sẵn trong bộ widget và họ chọn không dùng
(<https://support.tulip.co/docs/display-types>). Khuôn mẫu áp đảo là **một cột mỗi giờ cho
thực tế, định mức là một ĐƯỜNG phủ lên**
(<https://help.sap.com/docs/SAP_DIGITAL_MANUFACTURING/57088d83d7f24b71821704db82ba8cbd/0b748187bbc648dab73b856a4931764c.html>).

**Cần công bằng:** cột KHÔNG sai. Cột đơn — một lệnh, một cột mỗi giờ, một đường định mức
phủ lên — là đúng chuẩn ngành và giữ nguyên ưu điểm chống Bẫy C. Cái sai là **nhóm nhiều
lệnh vào cùng một cụm**.

**Thêm một điểm riêng của ta:** kế hoạch đã nhận ra **Bẫy C** — khung giờ không ghi sổ
không được nối liền — và dùng nó để biện minh cho cột. Lập luận đó đúng về *đường*, nhưng
không kéo theo *cột nhóm*. Cột đơn (một lệnh, một chuỗi giờ, có khoảng trống thật ở giờ
thiếu) giữ được ưu điểm ấy; **nhóm ba lệnh cạnh nhau thì không thêm gì cả** — nó chỉ làm
ba chuỗi cùng cạnh tranh một trục.

---

## 5 · Khuyến nghị cho biểu đồ "Đạt định mức theo giờ"

### 5.0 Bối cảnh cụ thể của hệ này

Kiểm tra lại schema trước khi khuyến nghị:

```
hourly_output: round_id · work_date · slot_hour · headcount · target_qty · qty · note
```
(`mes-backend/app/modules/production/models.py:51`)

Ba nhận xét quan trọng:

1. **Bảng `hourly_output` đã CHÍNH LÀ một Production Analysis Board.** `slot_hour` ·
   `target_qty` · `qty` · `note` là đúng bốn thứ LEI mô tả. Hệ đang ghi đúng cấu trúc
   lean mà không cần đổi gì.
2. **Cột `note` là cột "lý do" — nhưng là chữ tự do.** Trong khi đó hệ **đã có** bảng
   `reason_code` với nhóm `HOLD · NG · SHORT · QC · PACKING`
   (`mes-backend/app/common/vocab/enums.py:25`), gắn vào `line_segment.hold_reason_code_id`
   và các cột NG/SHORT. `hourly_output` là chỗ duy nhất dùng chữ tự do.
3. **Không có dữ liệu Six Big Losses.** Có `line_segment` với `kind = RUN | WAIT` và
   `started_at/ended_at`, tức là có **thời gian chạy và thời gian chờ**, có lý do chờ —
   nhưng không có "chạy chậm" hay "dừng vặt". Đủ cho Pareto lý do dừng, **không đủ** cho
   OEE waterfall thật (§2.5).

### 5.1 Ba nhóm người xem, ba dạng khác nhau

Không có một biểu đồ nào phục vụ được cả ba. Ép làm một cái là gốc của vấn đề.

| Người xem | Phạm vi | Câu hỏi họ hỏi | Dạng |
|---|---|---|---|
| **Công nhân ở trạm** | 1 lệnh đang làm | "giờ này tôi có kịp không, ca này còn kịp không" | **BẢNG theo giờ** + 1 thanh bullet cộng dồn |
| **Tổ trưởng** | 3–15 lệnh của tổ | "chuyền nào đang tụt, tụt từ giờ nào" | **small multiples** (≤ 25 ô) |
| **Điều độ** | 1 → 100+ lệnh | "hôm nay cả xưởng thế nào, ba lệnh tệ nhất là ai" | **1 số tổng + bảng sparkline sắp xếp được** |

---

### 5.2 Công nhân ở trạm — BẢNG, không phải biểu đồ

**Đây là khuyến nghị mạnh nhất của cả tài liệu.** Với người đứng ở trạm, dạng đúng là cái
mà lean đã dùng 50 năm: một **bảng**.

```
Lệnh MO-2419 · ngày 16/09 · trạm Sản xuất

Giờ     Người  Yêu cầu  Thực tế  Chênh   ∑Yêu cầu  ∑Thực tế  Đạt    Lý do
07–08     12      120      108     −12        120       108   90%    máy nén hụt hơi
08–09     12      120      124      +4        240       232   97%
09–10     11      110       —        —          —         —    —     (chưa ghi sổ)
10–11     12      120       96     −24        470       448   95%    thiếu vật tư
──────────────────────────────────────────────────────────────────────────────
Cộng dồn ca                                    470       448   95%   ✓ trên 85%
```

Vì sao bảng:

- LEI xếp nó là **problem-solving board**, và cột "Lý do" là lý do tồn tại của nó —
  <https://www.lean.org/lexicon-terms/production-analysis-board/>
- Công nhân **ghi vào** màn này mỗi giờ. Ô trống của bảng là lời nhắc; biểu đồ không có
  ô trống — <https://blog.gembaacademy.com/2008/03/13/101_kaizen_templates_production_control_board_1/>
- Chỉ có một phép so, và đọc hai con số cạnh nhau chính xác hơn ước lượng chiều cao cột.
- **Bẫy C tự biến mất.** Giờ chưa ghi sổ hiện là `—`, không thể nhầm với 0. Không biểu đồ
  nào làm được điều đó rõ bằng.

**Thêm đúng MỘT hình:** thanh **bullet chart** cho cộng dồn cả ca, dựng theo đặc tả Few
(<https://www.perceptualedge.com/articles/misc/Bullet_Graph_Design_Spec.pdf>):

```
Đạt định mức ca   ▏▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓█░░░░░░░░▏
                  0%        50%         85%↑        120%
                  └─ ba dải nền: 40% · 25% · 10% đen ─┘
```

- Thanh chính: đặc, dày ~⅓ chiều cao khung.
- Mốc **85%**: vạch ngắn **vuông góc** — đúng quy tắc comparative measure của Few.
  Không vẽ đường đứt đỏ chạy ngang cả biểu đồ.
- Ba dải nền: **một sắc đậm nhạt 40% · 25% · 10% đen**, KHÔNG dùng bốn token màu của app.
  Đây chính là lời giải cho **Bẫy D**: Few đã bác chuyện dùng nhiều sắc cho dải trạng thái,
  đúng vì lý do mù màu mà trình kiểm tra CVD đã báo.
- **Đoạn dự phóng cuối ca**: Few khuyến nghị tách thanh thành *thực tế đến lúc này* +
  *dự phóng theo nhịp hiện tại*, vì so với mục tiêu tương lai thì "it's not always so easy
  to tell if you are on track". Với ca sản xuất đây là tính năng đáng giá nhất — nó biến
  màn hình từ "báo cáo" thành "cảnh báo còn kịp cứu".

**Xác nhận từ hệ thương mại:** SAP dùng đúng **bullet chart** cho tiến độ lệnh
(<https://help.sap.com/docs/SAP_DIGITAL_MANUFACTURING/57088d83d7f24b71821704db82ba8cbd/024a9cdfb37e4b9ca4e2d52051f4426c.html>),
và con số đầu màn của họ là **Total Delta** — "how far behind or ahead the production progress
is at the current time", **âm thì in đỏ**
(<https://help.sap.com/docs/SAP_DIGITAL_MANUFACTURING/57088d83d7f24b71821704db82ba8cbd/d61b51c4a9c9489685e6ace2aa22b61b.html>).

Đáng cân nhắc lấy luôn: **thêm dòng `Chênh luỹ kế` bằng CÁI, không chỉ bằng phần trăm.**
"−22 cái" nói với công nhân nhiều hơn "95%", vì nó dịch thẳng ra việc phải làm bù.

**Nếu muốn thêm một biểu đồ theo giờ ở màn này** (không bắt buộc), dạng đúng theo chuẩn
ngành là **một cột mỗi giờ cho thực tế, định mức là một đường phủ lên** — đúng như SAP
`Line Monitor Shift Progress` với `Display Hourly Progress = ON`
(<https://help.sap.com/docs/SAP_DIGITAL_MANUFACTURING/57088d83d7f24b71821704db82ba8cbd/0b748187bbc648dab73b856a4931764c.html>).
**Một lệnh, một chuỗi cột.** Không nhóm.

---

### 5.3 Tổ trưởng — small multiples, tối đa 25 ô

Mỗi lệnh một ô nhỏ. Trong ô: **cột đơn theo giờ** (không phải cột nhóm), thang dọc chung
cho mọi ô, một vạch mảnh ở 85%.

```
┌─ MO-2419 ────────┐ ┌─ MO-2431 ────────┐ ┌─ MO-2455 ────────┐
│ ▁▄█▇▅█▇  ····85% │ │ █▇█▆▂▁▁  ····85% │ │ ▅█▇█▇██  ····85% │
│ 95%              │ │ 68%  ▲           │ │ 102%             │
└──────────────────┘ └──────────────────┘ └──────────────────┘
```

Quy tắc bắt buộc:

- **Chung thang dọc** — Analysis Function: *"All the numerical axes in a set of small
  multiple charts need to have the same scale to avoid misinterpretation"*
  (<https://analysisfunction.civilservice.gov.uk/policy-store/charts-a-checklist/>).
- **Trần 25 ô** — IBCS Chart template 13 (<https://www.ibcs.com/resource/chart-template-13/>).
  Quá 25 thì **chuyển sang §5.4**, không thu nhỏ ô thêm nữa.
- **Sắp xếp ô theo mức chênh, tệ nhất lên trước** — Analysis Function: *"Always rank by
  value"* (<https://analysisfunction.civilservice.gov.uk/policy-store/data-visualisation-charts/>).
  Đây là điểm mà thiết kế hiện tại thiếu hẳn.
- Giờ chưa ghi sổ: **cột trống có gạch chéo**, không phải cột cao 0.

---

### 5.4 Điều độ — một số tổng, rồi bảng sparkline sắp xếp được

Theo Shneiderman: *overview first, zoom and filter, then details-on-demand*
(<https://www.cs.umd.edu/~ben/papers/Shneiderman1996eyes.pdf>).

**Tầng 1 — một con số.**

```
Đạt định mức toàn xưởng hôm nay   93,4%      ✓ trên 85%
Σ thực tế 18.420 / Σ yêu cầu 19.720 · 7 lệnh dưới 85% · 12 khung giờ chưa ghi sổ
```

`Σqty ÷ Σtarget_qty`, **không phải trung bình của các phần trăm** — Bẫy A. Và dòng phụ
phải ghi rõ số khung bỏ ra vì `target_qty` NULL — Bẫy B.

**Tầng 2 — bảng có sparkline, sắp xếp theo mức chênh.**

```
Lệnh      Sản phẩm        Người  Theo giờ (07–19)        ∑YC    ∑TT   Đạt
MO-2431   Vỏ nhôm A2        14   █▇█▆▂▁▁▁·······        1.440  979   68%  ▼
MO-2508   Nắp chụp           8   ▆▅▄▃▂▂▁▁·······          960  672   70%  ▼
MO-2419   Khung thép        12   ▁▄█▇▅█▇████████        1.440 1.368   95%
…
```

- Sparkline là dạng duy nhất có nguồn cho hàng trăm thực thể trên một màn:
  Tufte nêu **500 sparkline trên một tờ A3**, hoạt động *"like sentences and paragraphs"*
  — <https://www.edwardtufte.com/notebook/sparkline-theory-and-practice-edward-tufte/>
- Cột số **đọc chính xác được**, sparkline chỉ để thấy dạng. Hai thứ này bổ nhau, đó là
  ý nghĩa gốc của sparkline: *"everywhere a word or number can be"*.
- **Sắp xếp mặc định: tệ nhất lên đầu.** Với 100 lệnh, điều độ chỉ cần 5 dòng đầu.
- Robbins đã chứng minh một danh sách xếp hạng chịu được ~60 thực thể trong một hình
  — <https://www.perceptualedge.com/articles/b-eye/dot_plots.pdf>

**Tầng 3 (tuỳ chọn) — heatmap lệnh × giờ.** Tab thứ hai, không phải màn mặc định. Thang
**phân kỳ hai sắc, điểm giữa trung tính đặt ở 85%**, đúng khuyến nghị của Few cho dữ liệu
chia hai phía (<https://www.perceptualedge.com/articles/b-eye/heatmaps.pdf>). Ô chưa ghi
sổ: **gạch chéo**, tuyệt đối không nằm trên thang màu. Bấm vào ô là mở bảng §5.2 của lệnh đó.

**Tầng 4 — bấm vào một lệnh** ra đúng màn §5.2. Đây là "details on demand".

---

### 5.5 Những thứ nên và chưa nên làm

| Việc | Kết luận | Lý do |
|---|---|---|
| **Pareto lý do dừng máy** | **làm được ngay** | `line_segment` có `kind=WAIT`, `hold_reason_code_id`, `started_at/ended_at` → cộng thời gian chờ theo mã lý do. Đây là Pareto đúng nghĩa Juran (<https://www.juran.com/wp-content/uploads/2021/03/The-Non-Pareto-Principle-1974.pdf>), và là màn Tulip có tài liệu đầy đủ nhất (<https://support.tulip.co/docs/performance-visibility-dashboard-1>). **Đặt ở màn riêng**, không nhét vào biểu đồ giờ — cả ba hệ SAP · Rockwell · Tulip đều tách (§3.7③) |
| **Dải trạng thái RUN/WAIT theo thời gian** | **nên làm, rẻ** | `line_segment` đã có đủ `kind` + `started_at/ended_at`. Đây là *state timeline* của Grafana (<https://grafana.com/docs/grafana/latest/visualizations/panels-visualizations/visualizations/state-timeline/>) và *Root Cause Analysis Gantt* của Rockwell (<https://literature.rockwellautomation.com/idc/groups/literature/documents/um/rptexp-um001_-en-e.pdf>). Nó trả lời "giờ đó hụt vì đứng máy hay vì chạy chậm" — câu mà biểu đồ sản lượng không trả lời được |
| **Pareto lý do không đạt định mức giờ** | **cần đổi schema** | `hourly_output.note` là chữ tự do; phải thêm `reason_code_id` trỏ `reason_code` với một nhóm mới. Không có mã thì không có Pareto |
| **OEE waterfall** | **chưa** | chỉ có RUN/WAIT, không có chạy chậm / dừng vặt. Dựng waterfall từ dữ liệu này là dựng một hình trông giống và sai (§2.5) |
| **Control chart / SPC trên tablet** | **không** | chưa ai được huấn luyện đọc. Và `target_qty` đổi từng giờ nên giới hạn phải răng cưa theo `nᵢ` (<https://www.spcforexcel.com/knowledge/attribute-control-charts/p-control-charts/>) — một biểu đồ không ai đọc được thì tệ hơn không có |
| **Run chart (quy tắc shift/crossings)** | **có, cho điều độ, giai đoạn 2** | không cần σ, báo động giả ~5% ổn định (<https://journals.plos.org/plosone/article?id=10.1371%2Fjournal.pone.0113825>). Hợp để cảnh báo "6 giờ liên tiếp dưới trung vị" thay vì la lên ở mỗi giờ đỏ |
| **`headcount` lên biểu đồ** | **không** | giữ nguyên quyết định trong kế hoạch: nó là cột trong bảng để đối chiếu, không phải mẫu số, không phải chuỗi |
| **Cột nhóm 3 lệnh** | **bỏ** | §4.4 |

### 5.6 Về dropdown gộp khung giờ `1h · 4h · 8h · 1 ngày`

Kế hoạch hiện tại cho dropdown này ở mọi màn. Khuyến nghị: **chỉ điều độ mới có nó.**

Lý do không phải kỹ thuật mà là mục đích. Bảng hour-by-hour tồn tại để bắt **đúng giờ nào**
hỏng, khi còn kịp cứu — LEI gọi nó là problem-solving board
(<https://www.lean.org/lexicon-terms/production-analysis-board/>). Gộp 8 giờ thành một cột
là xoá đúng cái thông tin đó: một ca 95% có thể giấu một giờ 40%. Với công nhân và tổ
trưởng, **1 giờ là hạt duy nhất có nghĩa**.

Gemba Academy còn cho thấy chiều ngược lại: dây chuyền tốc độ cao ghi mỗi
"five, ten or fifteen minutes", chậm thì "every two hours"
(<https://blog.gembaacademy.com/2008/03/13/101_kaizen_templates_production_control_board_1/>).
Hạt thời gian đi theo **nhịp quy trình**, không theo sở thích người xem.

Với điều độ nhìn cả tháng thì gộp là hợp lý — và khi gộp, bắt buộc
`Σqty ÷ Σtarget_qty`, không bao giờ là trung bình các phần trăm (Bẫy A).

### 5.7 Một nguyên tắc chung cho màn hình ngoài xưởng

Xưởng có ca đêm, màn hình treo tường, người đeo kính bảo hộ. Nguyên tắc **high-performance
HMI** trong họ tiêu chuẩn **ANSI/ISA-101.01-2015** *Human Machine Interfaces for Process
Automation Systems* (<https://www.isa.org/products/isa-101-01-2015-human-machine-interfaces-for>)
là: nền xám trung tính, **màu chỉ dành cho trạng thái bất thường**, giá trị trong ngưỡng
hiển thị nhạt, giá trị ngoài ngưỡng mới đậm và có màu.

Cần nói rõ: ISA-101.01 là tiêu chuẩn về **"cái gì"** — uỷ ban cố ý tách phần **"làm thế
nào"** sang các technical report riêng (<https://www.isa.org/intech/2020/september-october/isa-101-01-human-machine-interfaces-for-process-au>),
nên các quy tắc xám-và-màu-theo-ngoại-lệ ở trên là **thực hành high-performance HMI**, nguồn
thứ cấp (ví dụ <https://hmilibrary.com/standards/isa-101>), không phải trích nguyên văn
tiêu chuẩn.

Điều này khớp hoàn toàn với quy tắc màu của Few ở §2.1 và giải quyết Bẫy D theo hướng
đơn giản nhất: **đừng tô màu các chuỗi. Chỉ tô màu cái bất thường.**

---

## 6 · Tóm tắt một trang

1. **Hour-by-hour board là BẢNG.** Nguồn gốc là *Production Analysis Board* của LEI, đặt
   cạnh chuyền, và nó là **công cụ giải quyết vấn đề** — cột "lý do" quan trọng ngang cột số.
   <https://www.lean.org/lexicon-terms/production-analysis-board/>
2. **Cột chuẩn:** định mức giờ · định mức cộng dồn · thực tế giờ · thực tế cộng dồn · lý do ·
   đối sách · chữ ký quản lý. <https://www.leanproduction.com/win-the-shift/>
3. **Bullet chart** là dạng đúng cho "một số so với mục tiêu", có đặc tả gốc đầy đủ kể cả
   quy tắc màu chống mù màu và tính năng dự phóng.
   <https://www.perceptualedge.com/articles/misc/Bullet_Graph_Design_Spec.pdf>
4. **SPC phản đối phản ứng với điểm lẻ** vì mọi dữ liệu đều chứa nhiễu; phản ứng với nhiễu
   (tampering) làm kết quả xấu đi. <https://www.spcpress.com/pdf/DJW260.pdf>
5. **Trần số chuỗi là 3–4**, theo cả chuẩn chính phủ Anh lẫn IBCS. 100 lệnh vượt 25–50 lần.
   <https://analysisfunction.civilservice.gov.uk/policy-store/data-visualisation-charts/>
6. **Nhiều thực thể → small multiples (≤25) → bảng sparkline (hàng trăm) → heatmap để
   khoanh vùng**, luôn kèm một số tổng ở trên và đi sâu khi bấm.
   <https://www.cs.umd.edu/~ben/papers/Shneiderman1996eyes.pdf>
7. **Hệ thương mại làm: một cột mỗi giờ cho thực tế, định mức là ĐƯỜNG phủ lên; con số đầu
   màn là delta luỹ kế; mã lý do ở màn riêng.** SAP nói rõ nhất — kể cả chuyện định mức từng
   giờ *không đều nhau*, đúng như `target_qty` của ta.
   <https://help.sap.com/docs/SAP_DIGITAL_MANUFACTURING/57088d83d7f24b71821704db82ba8cbd/0b748187bbc648dab73b856a4931764c.html>
8. **Cột nhóm nhiều LỆNH là lựa chọn sai** cho màn này: nó tối ưu phép so trong cụm, trong khi
   câu hỏi của ta là so giữa các cụm; Few xếp cột vào quan hệ *Ranking* chứ không phải
   *Time Series*; trần "tối đa 3 lệnh" trong đặc tả là dấu hiệu chẩn đoán chứ không phải giải
   pháp; và **không hệ nào trong sáu hệ khảo sát làm thế**.
   <https://www.perceptualedge.com/articles/misc/Graph_Selection_Matrix.pdf>
   Nói cho công bằng: **cột đơn một lệnh thì đúng** — cái sai là gộp lệnh.
9. **Đổi trong kế hoạch hiện tại:** biểu đồ ② bỏ cột nhóm; thay bằng ba màn theo vai
   (bảng · small multiples · bảng sparkline); thêm dòng chênh luỹ kế bằng *cái*; thêm
   `reason_code_id` vào `hourly_output` nếu muốn có Pareto; và dropdown gộp khung giờ chỉ
   dành cho điều độ.
