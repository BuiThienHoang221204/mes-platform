# FE-REBUILD — Dựng lại `app/` và `components/` theo mockup

> Đọc cùng: `FE-PLAN.md` (luật) · `../mockup/index.html` (đặc tả màn hình) ·
> `../demo/BRD-v2-chot.md` (nghiệp vụ)
>
> Tài liệu này **chưa động vào code**. Nó trả lời: hiện đang mất gì, "giống mockup"
> nghĩa là giống đến đâu, làm theo thứ tự nào, đụng vào những tệp nào.

---

## 1. Phân tích vấn đề hiện tại

### 1.1 Cái gì còn, cái gì mất

Xoá `src/app/` và `src/components/` **không phải** là về vạch xuất phát. `src/` còn
**39 tệp** — toàn bộ tầng dữ liệu còn nguyên:

| Thư mục | Còn | Nội dung |
| --- | :---: | --- |
| `src/constants/` | ✅ 6 tệp | `queryKeys` · `errorCodes` · `roles` (`permissionFor`) · `stations` · `flow` · `status` |
| `src/hooks/` | ✅ 11 tệp | `useQueue` `useAtStation` `useCounts` `useRunning` `useScan` `useTrace` `useLines` `useProductionActions` `useHandover` `useQcDecide` `useWarehouseIn` `useWakeLock` `useScanInput` |
| `src/services/` | ✅ 7 tệp | axios + interceptor refresh, 6 service theo miền |
| `src/stores/` | ✅ 4 tệp | đúng bốn store §4.2 |
| `src/schemas/` `src/types/` `src/utils/` | ✅ 8 tệp | zod, kiểu response, format |
| `src/context/` | ✅ 3 tệp | `QueryProvider` `ThemeProvider` `ToastProvider` |
| `public/` | ✅ | fonts SVN-Gilroy · manifest · sw.js · bộ icon PWA · logo Amphenol |
| `tailwind.config.ts` | ✅ | thang chữ, weight cap 600, token màu, `minHeight: touch 56px` |
| **`src/app/`** | ❌ | **mất hết** — routes, `layout.tsx`, **`globals.css`** |
| **`src/components/`** | ❌ | **mất hết** — chưa từng có bộ `ui/` hoàn chỉnh |

### 1.2 Mất mát bị giấu: tầng token

Đây là chỗ nguy hiểm nhất và không nhìn thấy ngay.

`tailwind.config.ts` **sống sót**, nhưng nó không định nghĩa giá trị nào cả — nó chỉ
trỏ vào biến CSS:

```ts
colors: { bg: "var(--color-bg)", surface: { DEFAULT: "var(--color-surface)" }, … }
fontSize: { body: ["var(--text-body)", …] }
borderRadius: { field: "var(--r-sm)", card: "var(--r-md)" }
```

**49 biến** này được định nghĩa trong `src/app/globals.css` — tệp vừa bị xoá cùng thư
mục. Hệ quả: `pnpm build` vẫn **chạy sạch**, Tailwind vẫn sinh class `bg-surface`,
nhưng `var(--color-surface)` là `undefined` → nền trong suốt, chữ đen trên đen.

> Lỗi này không có thông báo. Nó chỉ hiện ra khi mở trình duyệt và thấy trang trắng
> toát. Nên việc đầu tiên phải làm là dựng lại `globals.css` cho **khớp từng tên biến**
> với `tailwind.config.ts`, không phải viết một bộ token mới.

Ba tệp sống sót đang **phụ thuộc hợp đồng** vào `globals.css`:

| Tệp | Trông chờ gì ở `globals.css` |
| --- | --- |
| `tailwind.config.ts` | đủ 49 biến, đúng tên |
| `ThemeProvider.tsx` | đổ lớp `.dark` lên `<html>` → cần khối `.dark { … }` · đặt `--fs` → cần `calc(… * var(--fs))` |
| `ToastProvider.tsx` | `env(safe-area-inset-top)` (R33) |

### 1.3 Lệch giữa mockup và thực tế backend

Mockup là **bản mô phỏng chạy bằng dữ liệu cứng**. Bốn chỗ nó làm được mà app thật
thì không, phải xử lý trước khi bê sang:

| # | Mockup làm | Thực tế | Xử lý |
| --- | --- | --- | --- |
| 1 | Nút **`Đổi vai`** đổi giữa 13 vai | Vai đến từ `POST /auth/login` → `useSessionStore` | **Bỏ hẳn** nút này. Thay bằng màn `/login`. Xem §6.1 |
| 2 | Trạm suy ra từ **vai đang chọn** | Trạm đến từ **THIẾT BỊ** — `X-Station-Token` (R22) | Trạm đọc `useStationStore`. Máy chưa cấu hình → màn "Thiết bị chưa đăng ký trạm" |
| 3 | Ô quét **tự đọc mã, tự quyết nhận/chặn** ở client | `POST /scan` — server quyết, trả `{code, message}` | FE chỉ chuẩn hoá chuỗi (`utils/moCode.ts` đã có), rẽ nhánh bằng `err.code` |
| 4 | Nút **`Accept tất cả (3)`** ở Kho xuất | **Backend KHÔNG có endpoint này.** Chỉ có `POST /warehouse-out/handover-batch` | Xem câu hỏi Q2 §7 |

Điểm 4 là phát hiện đáng kể: BRD §1b.4 chốt Kho có **cả hai** nút hàng loạt, nhưng
backend mới làm `handover-batch`. `Accept tất cả` chưa có chỗ gọi.

### 1.4 Lệch giữa mockup và FE-PLAN

| Chủ đề | Mockup | FE-PLAN | Ai thắng |
| --- | --- | --- | --- |
| Font | IBM Plex Sans/Mono | SVN-Gilroy + Google Sans Flex (§6.4) | **FE-PLAN** |
| Màu | teal `#0C6B7A` tự chế | token roomify, cấm hardcode (R32) | **FE-PLAN** |
| Cỡ chữ | 14px gốc | `--fs: 1.15` → body 17.3px, tối thiểu 16px (R29, §1) | **FE-PLAN** |
| Theme | sáng mặc định | **tối** mặc định (R32) | **FE-PLAN** |
| Icon | emoji + SVG inline | Phosphor qua `PhosphorIcons.tsx` (R18) | **FE-PLAN** |
| Tổ chức code | 1 tệp `screens.js` 816 dòng | ≤200 dòng/tệp, ba tầng component (§6.1, §6.2) | **FE-PLAN** |
| Vùng chạm | ~32px | ≥56px (§1) | **FE-PLAN** |

Mockup thắng ở đúng một thứ, nhưng là thứ quan trọng nhất: **bố cục và luồng**.

---

## 2. Giải thích đúng yêu cầu

Tôi hiểu yêu cầu là:

> Dựng lại `app/` và `components/` sao cho **người dùng đi qua đúng các màn hình và
> đúng thứ tự như mockup**, còn **hình thức thì theo FE-PLAN**.

Nói cách khác, "giống mockup" = giống **bố cục · điều hướng · thông tin trên màn**,
**không** phải giống **màu · font · khoảng cách**.

Lý do tôi đọc như vậy chứ không phải chép nguyên mockup:

- FE-PLAN tự nhận là **"luật, không phải gợi ý"**, và §6.4 chép hệ token từ
  `roomify-ui` để MES trông cùng một nhà với sản phẩm kia. Chép skin của mockup là
  phá thẳng điều đó.
- Mockup dựng cho **người duyệt nghiệp vụ ngồi xem trên laptop**. App thật chạy trên
  **máy tính bảng, người đeo găng, xưởng chói**. Chữ 14px và nút 32px của mockup
  không dùng được ngoài xưởng — đó là §1 của FE-PLAN.
- Mockup nhét đầy **khối ghi chú trích BRD** ("vì sao QC FAIL về Kho", "vì sao ba ô
  SL phải cộng đúng"). Đó là công cụ để duyệt thiết kế. Đưa nguyên vào app thật thì
  người vận hành phải cuộn qua ba đoạn văn mới tới cái bảng họ cần.

**Nếu tôi đọc sai** — tức là bạn muốn giữ nguyên cả màu và font của mockup — thì nói
trước khi tôi bắt đầu, vì nó đổi hẳn §3.1 và làm FE-PLAN §6.4 thành vô hiệu.

### Cái gì từ mockup được bê nguyên sang

1. **Sidebar ba nhóm** — `Trạm của tôi` · `Xem chung` · `Tra cứu`, nhãn `chỉ xem` trên
   mục Step 4 khi vai không có quyền ghi.
2. **Trang `Quét nhận` gộp hàng đợi + ô quét**, thanh quét đứng đầu trang, phản hồi
   một dòng ngay trong thanh, hàng đợi full width.
3. **Bảng `Đang ở bước N`** — khớp đúng `GET /board/at/{station}` mà backend đã có.
4. **Stepper rẽ nhánh của Step 4** — ba bước tuần tự rồi tách hai làn song song. Đây là
   thứ giá trị nhất của mockup và là chỗ dễ làm sai nhất nếu dựng lại từ đầu.
5. **Bấm dòng hàng đợi để nạp mã vào ô quét** (không nhận luôn).
6. **Ba bảng nhật ký đủ cột** theo schema §7.2b / §7b.2 / §9.

---

## 3. Phương án giải quyết

### 3.1 Nguyên tắc: tách "bố cục" khỏi "da"

Với mỗi màn của mockup, tôi lấy ra ba thứ và bỏ phần còn lại:

```
GIỮ    cấu trúc khối  (khối nào trên khối nào, cột trái/phải, thứ tự đọc)
GIỮ    dữ liệu hiện ra (cột nào, badge nào, con số nào)
GIỮ    luồng bấm      (bấm gì ra gì, thứ tự các bước)
BỎ     màu · font · px · khối ghi chú trích BRD
```

Ghi chú BRD không vứt đi hết — phần nào **người vận hành cần biết lúc đang thao tác**
thì rút thành một dòng microcopy dưới ô nhập. Phần nào là lý lẽ thiết kế thì để lại
trong mockup, đó mới là chỗ của nó.

### 3.2 Đối chiếu màn hình mockup → route

| Mockup | Route | API |
| --- | --- | --- |
| `wh_out/scan` | `/warehouse-out` | `board/queue/0` + `board/at/0` + `POST /scan` |
| `wh_out/handover` · `slip` | cùng trang, khối dưới | `POST /warehouse-out/{code}/handover` · `handover-batch` |
| `setup/scan` · `working` | `/setup` | `queue/1` · `at/1` · `/scan` — **không có endpoint riêng** (§8.1) |
| `qc/scan` · `decide` | `/qc` | `queue/2` · `at/2` · `POST /qc/{code}` |
| `waiting/scan` · `dispatch` | `/waiting` | `queue/3` · `at/3` — **không có endpoint riêng** |
| `prod/*` (7 màn) | `/production` | `queue/4` · `at/4` · `lines/*` · `production/close` · `hourly` · `packing/*` |
| `wh_in/scan` · `finish` | `/warehouse-in` | `queue/5` · `at/5` · `POST /warehouse-in/{code}/complete` |
| `planner/create` · `book` | `/mos` | `POST /mos` · `/mos/import` · `/submit` · `/cancel` · `GET /mos` |
| `planner/dash` | `/mos` (khối đầu) | `GET /board/counts` |
| `shared/board` · `planner/board` | `/running` | `GET /board/running` — refetch 10s |
| `shared/trace` · `planner/trace` | `/mos/[code]/trace` | `GET /mos/{code}/trace` |
| `shared/step4` (chỉ xem) | `/production?view=1` | cùng API, ẩn nút theo `permissionFor` |
| `shared/map` (Luồng) | **bỏ trang riêng** | thay bằng dải `flow.ts` inline — xem dưới |

**Bỏ trang `Luồng toàn quy trình`.** `src/constants/flow.ts` đã có sẵn `STATION_FLOW`
với `from / here / next / back` cho từng trạm. Hiện ba dòng đó **ngay trên trang của
trạm** thì người đứng trạm đọc được lúc họ cần; bắt họ rời trạm sang một trang sơ đồ
thì không ai mở. Tệp `flow.ts` được viết đúng cho mục đích này.

### 3.3 `/scan` là cửa vào, không phải màn riêng

R26 chốt `start_url` của PWA là `/scan`. Nhưng §8.2 lại nói màn của trạm gồm "hàng đợi
+ ô quét + đồng hồ bước" — tức ô quét nằm **trong** trang trạm, đúng như mockup.

Giải: `/scan` là **redirect mỏng** → `stationRoute(station)` đọc từ `useStationStore`.
Hàm `stationRoute()` đã có sẵn trong `constants/stations.ts`.

```
mở PWA → /scan → đọc station của thiết bị → redirect /qc
chưa cấu hình trạm → màn "Thiết bị chưa đăng ký trạm" (R22)
```

### 3.4 Tổ chức component — ba tầng, trần 200 dòng

Mockup là một tệp 816 dòng. Cắt theo §6.2:

```
components/ui/         AppButton AppCard AppInput AppSelect AppModal
                       StatusPill StationBadge RoundBadge QtyStat
                       EmptyState ErrorState            ← §6.3, làm TRƯỚC mọi màn
components/common/     AppHeader StationSidebar FlowHint StepFlow ForkFlow
                       ConfirmDialog PwaInstallPrompt
components/scan/       ScanBar ScanFeedback CameraModal QueueList QueueRow
components/station/    AtStationTable HandoverTable SlipCard QcDecideForm
components/production/ LinePicker RunBoard ParallelLanes HourlyForm HourlyLog
                       CloseBookForm
components/packing/    PackStartCard PackHourlyForm PackHourlyLog PackFinishForm
components/board/      RunningTable CountsTiles
components/mo/         MoCreateForm MoImportForm MoTable RoundTable
                       StepTimerTable EventLogTable
```

Hai component đáng chú ý vì chúng mang giá trị riêng của mockup:

- **`StepFlow`** — stepper tuần tự, đánh số, dùng cho 5 trạm.
- **`ForkFlow`** — stepper rẽ nhánh **chỉ cho trạm 4**: ba bước có số rồi tách hai làn
  `Chuyền` ‖ `Đóng thùng`, **trong làn không đánh số** vì số ngụ ý thứ tự mà hai làn
  chạy cùng lúc (§7b).

---

## 4. Đề xuất ưu tiên

Bám lộ trình FE-PLAN §9, nhưng chèn lại **P0** vì tầng token đã mất.

| # | Giai đoạn | Nội dung | Xong khi |
| :---: | --- | --- | --- |
| **P0** | **Tầng token + vỏ app** | `globals.css` (49 biến, khớp `tailwind.config.ts`) · `layout.tsx` + script chống FOUC · nối 3 provider · `/login` · `/station-setup` | Mở trình duyệt thấy đúng màu, đổi theme/cỡ chữ ăn, đăng nhập thật chạy |
| **P1** | Bộ component | 11 component `ui/` §6.3 + `PhosphorIcons.tsx` + `IconProvider` · trang `/dev/kit` | `/dev/kit` xem đủ mọi biến thể |
| **P2** | Vỏ trạm + trạm 0 | `StationLayout` + `StationSidebar` + `/scan` redirect + `ScanBar` + `QueueList` + `AtStationTable` · **trạm 0 hoàn chỉnh** | Quét bằng đầu đọc thật, đi từ nhận tới bàn giao |
| **P3** | Trạm 1 · 2 · 3 · 5 | Nhân bản khung P2 · `QcDecideForm` · `WarehouseInFinish` | Đi hết một vòng MO trên UI |
| **P4** | Trạm 4 đầy đủ | `ForkFlow` · `LinePicker` · `RunBoard` · `ParallelLanes` · sản lượng giờ · chốt sổ 3 số · đóng thùng | Chạy đúng kịch bản `3.000 pcs · 800/thùng` |
| **P5** | Kế hoạch + Bảng | `/mos` tạo/import/submit/huỷ · `/running` treo tường · `/mos/[code]/trace` | Bảng tự cập nhật 10s |
| **P6** | Hoàn thiện | `/catalog/lines` · `/account` (theme, cỡ chữ) · rà §10 | Checklist §10 sạch |

**Vì sao P0 phải đứng trước:** không có `globals.css` thì mọi component dựng ở P1 đều
không kiểm tra được bằng mắt — build sạch mà màn hình trắng.

**Vì sao P2 nặng hơn vẻ ngoài của nó:** FE-PLAN §9 ghi *"Giai đoạn 2 là quan trọng
nhất — làm xong một trạm cho thật đúng rồi nhân bản, đừng làm sáu trạm cùng lúc ở mức
70%."* P3 gần như chỉ là điền chỗ trống nếu P2 làm đúng.

---

## 5. Các tệp cần thay đổi

### 5.1 Tạo mới — P0

```
src/app/globals.css                    ★ 49 token, light + .dark, --fs, @font-face
src/app/layout.tsx                     ★ metadata, manifest, script chống FOUC, providers
src/app/page.tsx                         redirect → /scan
src/app/(auth)/login/page.tsx
src/app/(auth)/station-setup/page.tsx    R22 — máy chưa đăng ký trạm
src/components/ui/AppButton.tsx  AppCard  AppInput  AppSelect  AppModal
src/components/ui/StatusPill.tsx  StationBadge  RoundBadge  QtyStat
src/components/ui/EmptyState.tsx  ErrorState
src/components/common/PhosphorIcons.tsx  ★ R18 — cửa duy nhất cho icon
```

★ = chặn mọi thứ khác, làm trước.

### 5.2 Tạo mới — P2 → P6

```
src/app/(station)/layout.tsx             StationLayout + sidebar
src/app/(station)/scan/page.tsx          redirect theo stationRoute()
src/app/(station)/warehouse-out/page.tsx
src/app/(station)/setup/page.tsx
src/app/(station)/qc/page.tsx
src/app/(station)/waiting/page.tsx
src/app/(station)/production/page.tsx
src/app/(station)/warehouse-in/page.tsx
src/app/(planner)/mos/page.tsx
src/app/(planner)/catalog/lines/page.tsx
src/app/(board)/running/page.tsx
src/app/(board)/mos/[code]/trace/page.tsx
src/app/account/page.tsx                 ThemeControls (R30, R32)
src/app/dev/kit/page.tsx                 P1
src/components/common/*                  StationSidebar FlowHint StepFlow ForkFlow …
src/components/{scan,station,production,packing,board,mo}/*
```

### 5.3 Sửa tệp đang có

| Tệp | Sửa gì |
| --- | --- |
| `src/hooks/usePwaInstall.ts` | **chưa có** — FE-PLAN §6.6 yêu cầu. Tạo mới |
| `src/constants/queryKeys.ts` | thêm `boardKeys.at(station)` nếu chưa có (cần cho `/board/at/{n}`) |
| `src/hooks/board/useBoard.ts` | kiểm `useAtStation` đã trả đúng kiểu — đã có, chỉ đối chiếu |
| `tailwind.config.ts` | **không sửa** — `globals.css` phải khớp theo nó, không phải ngược lại |

### 5.4 Không đụng tới

`src/services/` · `src/stores/` · `src/schemas/` · `src/types/` · `src/utils/` ·
`src/context/` · `public/`. Tầng này còn nguyên và đúng; sửa nó là tự tạo việc.

---

## 6. Cách triển khai cụ thể

### 6.1 P0 — dựng lại `globals.css`

Không sáng tác bộ token mới. Trình tự:

1. Trích danh sách biến từ `tailwind.config.ts` (đã làm — **49 biến**).
2. Viết `:root { … }` cho light, `.dark { … }` cho dark, đúng 49 tên đó.
3. Thang chữ giữ **nguyên công thức** `calc(… * var(--fs))` và `--fs: 1.15` (R29).
4. `@font-face` SVN-Gilroy trỏ `/fonts/SVN-Gilroy-SemiBold.otf` (tệp đã có trong `public/`).
5. Bảng màu lấy theo `roomify-ui`; mockup chỉ dùng để **đối chiếu vai trò** của từng
   token (đâu là `surface`, đâu là `line`, đâu là `ok/warn/danger`), không lấy mã màu.

Sau đó `layout.tsx` với script chống FOUC — **luật sáng/tối phải khớp từng chữ với
`ThemeProvider.tsx`** (R32), vì `ThemeProvider` đang dùng:

```ts
document.documentElement.classList.toggle("dark", theme === "dark" || (theme === "system" && mq.matches))
```

Script inline phải ra **đúng cùng kết quả**, nếu không app nháy một nhịp mỗi lần mở
với người để `system`.

**Cách tự kiểm P0:** mở `/dev/kit`, bấm nút đổi cỡ chữ — **mọi** chữ trên màn phải
to/nhỏ theo. Chỗ nào đứng yên là chỗ đó hardcode `text-[15px]`, vi phạm R32.

### 6.2 P2 — khung một trạm, bê từ mockup

Trang trạm = bốn khối xếp dọc, đúng thứ tự mockup:

```
┌ FlowHint ─────── from → here → next (+ back nếu có) — từ flow.ts
├ StepFlow ─────── stepper các bước của trạm
├ ScanBar ──────── ô quét + Camera + Nhận · ScanFeedback một dòng bên trong
├ QueueList ────── hàng đợi FULL WIDTH · bấm dòng → nạp mã vào ô quét
└ AtStationTable ─ "Đang ở bước N" · không có nút "xong" (§8.2)
```

Bốn điểm phải làm đúng, đây là chỗ mockup nói đúng mà dễ dựng sai:

- **Ô quét auto-focus và giành lại focus** (§1). Đầu đọc gõ phím rồi `Enter` — dùng
  `useScanInput.ts` đã có sẵn.
- **`Enter` = bấm Nhận.** Không có nút nào chen giữa.
- **Bấm dòng hàng đợi chỉ nạp mã**, không nhận luôn — §1b đã bỏ nút Accept từng dòng
  vì nhiều đơn thì bấm trúng MO bên cạnh.
- **Phản hồi nằm trong thanh quét**, một dòng. Lỗi bắn thêm toast (R33 — toast ở **đầu**
  trang).

Xử lý lỗi: rẽ nhánh bằng `err.code`, hiện `err.message` **nguyên văn** (R12).

```ts
if (err.code === Err.SKIP_STEP)    // chưa xong trạm trước
if (err.code === Err.NO_HANDOVER)  // Kho chưa bàn giao
if (err.code === Err.STEP_DUP)     // trạm này quét rồi
```

### 6.3 P4 — trạm 4, chỗ khó nhất

`ForkFlow` dựng theo đúng mô hình mockup:

```
① Quét nhận  ② Chọn line  ③ Bảng đang chạy ─┬─ CHUYỀN ───── Sản lượng giờ · Chốt sổ SX
                        (bấm Đang lắp ráp)   └─ ĐÓNG THÙNG ─ Bắt đầu·theo giờ · Kết thúc
```

Ba luật không được phá:

1. **Trong làn không đánh số.** Số là ký hiệu của thứ tự; hai làn chạy cùng lúc.
2. **`Bắt đầu đóng thùng` mở khi ≥1 line `Đang lắp ráp`**, không chờ chốt sổ SX.
3. **`Kết thúc đóng thùng` chặn tới khi `Chốt sổ SX` xong** — ràng buộc **duy nhất**
   giữa hai làn.

Hai chỗ phải dùng **số server trả, không tự tính** (R23):

- `packed_pcs` · `made_pcs` · **`le_pcs`** từ `POST /packing/{code}/hourly`.
- `le_pcs` bắt buộc hiện kèm chữ **"chưa đủ thùng, KHÔNG phải hàng thiếu"** — chỗ
  người vận hành hiểu nhầm nhiều nhất, hiểu nhầm là đi báo thiếu hàng.

Form chốt sổ: hiện **tổng sống** khi gõ (`Σ 2.000 — khớp` / `Σ 1.995 — hụt 5`) nhưng
**không chặn ở FE** — mục tiêu vòng nằm ở server và đổi theo vòng, kiểm ở FE là có hai
luật và luật FE sai trước (R8).

### 6.4 Rà từng màn trước khi đóng

Mỗi màn xong chạy checklist §10 của FE-PLAN. Ba dòng hay trượt nhất:

```
[ ] Màn hiện số liệu có RoundBadge          ← mockup có badge "Vòng 2", đừng bỏ
[ ] Vùng chạm ≥ 56px · chữ ≥ 16px           ← mockup 32px/14px, KHÔNG bê sang
[ ] Không tệp nào > 200 dòng                ← screens.js của mockup 816 dòng
```

---

## 7. Cần bạn chốt trước khi tôi gõ code

| # | Câu hỏi | Đề xuất của tôi |
| :---: | --- | --- |
| **Q1** | "Giống mockup" là giống **bố cục + luồng** (giữ font/màu FE-PLAN), hay giống cả **màu + font**? | **Bố cục + luồng.** FE-PLAN §6.4 là luật, và mockup 14px/32px không dùng được ngoài xưởng |
| **Q2** | Nút `Accept tất cả` của Kho — backend chưa có endpoint. Bỏ nút, hay chờ backend làm? | **Tạm bỏ**, giữ `Bàn giao tất cả` (có `handover-batch`). Ghi vào việc tồn của backend |
| **Q3** | Có cần **nút đổi vai cho môi trường dev** để bạn/khách duyệt nhanh 13 vai không? | **Có, nhưng chỉ ở `/dev/`**, gate bằng `NODE_ENV !== "production"` |
| **Q4** | Khối ghi chú trích BRD trong mockup — bỏ hết, hay giữ dạng thu gọn? | **Bỏ khỏi màn thao tác.** Phần cần lúc thao tác rút thành một dòng microcopy |

Và **bốn câu §11 của FE-PLAN vẫn chưa ai trả lời** — chúng thuộc loại *trả lời sai thì
phải viết lại nhiều màn*:

1. FE và BE **cùng site** qua reverse proxy? → quyết `samesite` và có cần CSRF không.
2. Máy tính bảng ở trạm dùng **tài khoản chung** hay mỗi người một tài khoản? → nếu
   chung thì cần màn "chọn người" mỗi thao tác để `closed_by` còn đúng.
3. Bảng treo tường có **chạy không cần đăng nhập** không? → cần vai chỉ-xem, backend chưa có.
4. Xưởng có **wifi chập chờn** không? → nếu có thì `/scan` cần hàng đợi offline, việc lớn.

Câu **2** ảnh hưởng ngay từ P0 (màn `/login`). Ba câu còn lại chậm nhất phải chốt
trước P5.
