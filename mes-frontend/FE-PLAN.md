# FE-PLAN — Kế hoạch & Quy tắc Frontend MES

> Backend: `../mes-backend` (FastAPI, đã chạy tới migration `0006`)
> Nghiệp vụ: `../demo/BRD-v2-chot.md` v2.23 · CSDL: `../demo/DB-GON.md` v2.9
> Demo đối chiếu UI: `../demo/mes-v2-console.html` — **đây là bản đặc tả màn hình chính xác nhất đang có**
> Tham khảo cách phân tách component: `D:\Freelance\roomify-systems\roomify\roomify-ui`

Tài liệu này là **luật**, không phải gợi ý. Đọc hết §1–§3 trước khi gõ dòng code đầu tiên; §1 quyết
định mọi thứ còn lại.

---

## 1. Xưởng quyết định giao diện, không phải ngược lại

Năm ràng buộc dưới đây sinh ra gần hết các quy tắc ở §4–§6. Bỏ qua chúng là viết một cái web đẹp mà
không ai ngoài xưởng dùng được.

| Ràng buộc | Hệ quả bắt buộc lên FE |
| --- | --- |
| **Máy tính bảng, người đeo găng, xưởng chói** | Vùng chạm tối thiểu **56px**, chữ tối thiểu **16px** (đạt bằng `--fs: 1.15`, R29), tương phản cao. Không hover-only, không tooltip mang thông tin |
| **Quét QR là thao tác chính** (§1b) | Ô nhập mã phải **auto-focus và luôn giành lại focus**. Đầu đọc gõ phím rồi Enter — không có nút bấm nào chen giữa |
| **Một MO chạy nhiều VÒNG** (§6b) | Mọi màn hình hiện số liệu phải ghi rõ **đang xem vòng nào**. Số của vòng 1 và vòng 2 không được trộn |
| **PCS là đơn vị gốc, THÙNG chỉ là cách đếm** (§7b.2) | FE **không bao giờ** tính tiến độ bằng thùng. Xem §7.4 |
| **13 vai, quyền theo TRẠM** (§9b) | FE ẩn/hiện theo vai là để **đỡ bấm nhầm**, không phải để bảo mật. Backend vẫn chặn |

> **Câu hỏi tự kiểm khi thiết kế một màn hình:** *người đeo găng tay, đứng cạnh chuyền ồn, có làm xong
> việc này trong 3 chạm không?* Không thì thiết kế lại, đừng thêm hướng dẫn.

---

## 2. Stack và vì sao chọn

| Lớp | Chọn | Vì sao |
| --- | --- | --- |
| Framework | **Next.js 15 (App Router)** + TypeScript | Đồng bộ với `roomify-ui`, team đã quen |
| Style | **TailwindCSS** + token CSS var | Không hardcode màu/px — xem §6.4 |
| Font | **SVN-Gilroy** (tiêu đề) + **Google Sans Flex** (nội dung) | Chép nguyên hệ từ `roomify-ui/globals.css` — xem §6.4 |
| Dữ liệu SERVER | **TanStack Query v5** | Cache, invalidate, retry, `isFetching` — thứ MES cần nhất vì mọi màn đều là bảng sống |
| Dữ liệu CLIENT | **Zustand** | Chỉ cho 4 thứ ở §4.2. Không hơn |
| Form | **react-hook-form + zod** | Validate phải khớp backend hai chiều (§4.3) |
| HTTP | **Axios** | Interceptor 401 → refresh; cookie httpOnly |
| Icon | **@phosphor-icons/react** `^2.1.7`, khai báo tập trung | Không SVG inline · không import rải rác (§6.5) |
| PWA | **manifest + service worker viết tay** (không `next-pwa`) | Máy tính bảng ở trạm cài ra màn hình chính, chạy toàn màn (§6.6) |

Không dùng: Redux (thừa), SWR (trùng TanStack), `fetch` trần trong component (cấm, §4.1),
**`next-pwa`** (xem §6.6 để biết vì sao).

**Một bộ icon duy nhất — Phosphor.** Trộn hai bộ là hai phong cách nét trên cùng một màn, và người
sau sẽ không biết icon mới nên lấy ở đâu.

```bash
pnpm add @tanstack/react-query zustand react-hook-form @hookform/resolvers zod axios @phosphor-icons/react
pnpm add -D sharp                      # sinh bộ icon PWA
```

```bash
pnpm dev          # cổng 3000
pnpm lint
pnpm build        # phải sạch 100% trước khi bàn giao
```

Env:
```
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/v1
```

---

## 3. LUẬT VÀNG — dữ liệu nào sống ở đâu

Đây là quy tắc **hay bị phá nhất** và phá nó là hỏng cả dự án: người ta lấy dữ liệu từ API rồi nhét
vào Zustand "cho tiện", thế là có hai nguồn sự thật và không ai biết cái nào mới.

```
Dữ liệu từ API          →  TanStack Query   ·  KHÔNG BAO GIỜ vào Zustand
Giá trị đang gõ trong form →  react-hook-form ·  KHÔNG dùng useState rời
Bộ lọc / tab / trang    →  URL searchParams ·  để F5 và chia sẻ link vẫn đúng
Thứ còn lại (rất ít)    →  Zustand          ·  xem danh sách đóng ở §4.2
```

**Bài kiểm một câu:** *nếu F5 trang thì giá trị này có phải lấy lại từ server không?*
Có → TanStack Query. Không → một trong ba chỗ còn lại.

> **Phản ví dụ đúng của MES:** danh sách hàng đợi trạm 4. Cám dỗ là `useEffect` gọi API rồi
> `setState`. Làm vậy thì: hai tab lệch nhau, bấm "Nhận" xong bảng không tự cập nhật, và mỗi lần vào
> lại màn là màn hình trắng. Dùng `useQuery` thì cả ba vấn đề biến mất mà không viết thêm dòng nào.

---

## 4. Quy tắc từng công nghệ

### 4.1 TanStack Query

**R1 — Cấm fetch trong component.** Mọi truy vấn/mutation bọc trong custom hook ở `src/hooks/`.
Component chỉ gọi hook. Lý do: cùng một dữ liệu bị gọi ở 3 màn với 3 cách xử lý lỗi khác nhau là
chuyện chắc chắn xảy ra nếu không có luật này.

**R2 — Query key lấy từ factory, cấm gõ chuỗi tay.** Một tệp duy nhất `src/constants/queryKeys.ts`:

```ts
export const boardKeys = {
  all: ["board"] as const,
  running: () => [...boardKeys.all, "running"] as const,
  queue: (station: number) => [...boardKeys.all, "queue", station] as const,
  counts: () => [...boardKeys.all, "counts"] as const,
};
export const moKeys = {
  all: ["mo"] as const,
  detail: (code: string) => [...moKeys.all, "detail", code] as const,
  trace: (code: string) => [...moKeys.all, "trace", code] as const,
};
export const catalogKeys = {
  lines: () => ["catalog", "lines"] as const,
  reasons: (group?: string) => ["catalog", "reasons", group ?? "all"] as const,
};
```

Gõ tay `["board","counts"]` ở chỗ này và `["board-counts"]` ở chỗ kia thì `invalidateQueries` trượt —
và nó **trượt im lặng**, không báo lỗi gì.

**R3 — Bảng invalidate là hợp đồng, phải khai ở một chỗ.** MES có đặc thù: **mọi hành động ở trạm đều
đổi hàng đợi và con số trên thanh trạm.** Quên invalidate là người ở trạm sau không thấy việc.

| Mutation | Invalidate |
| --- | --- |
| `POST /scan` | `boardKeys.all` · `moKeys.trace(code)` |
| Mọi thao tác trạm (handover · qc · line · production · packing · warehouse-in) | `boardKeys.all` · `moKeys.detail(code)` · `moKeys.trace(code)` |
| `POST /mos`, `/mos/bulk`, `/mos/{code}/submit`, `/cancel` | `boardKeys.all` · `moKeys.all` |
| `POST /lines` · `DELETE /lines/{code}` | `catalogKeys.lines()` |

> Viết một helper `invalidateStation(qc, code)` dùng chung cho mọi mutation trạm. Đừng chép 3 dòng
> `invalidateQueries` vào 12 hook.

**R4 — `staleTime` theo bản chất dữ liệu, không để mặc định cho tất cả.**

| Dữ liệu | staleTime | refetchInterval |
| --- | --- | --- |
| `catalog/lines`, `catalog/reasons` | `Infinity` | không |
| `board/counts`, `board/queue`, `board/running` | `0` | **10s** — bảng treo tường phải sống |
| `mos/{code}`, `mos/{code}/trace` | `30s` | không |

**R5 — Bảng đang chạy dùng `refetchInterval`, KHÔNG dùng `setInterval` + refetch tay.** Query tự dừng
khi tab ẩn; `setInterval` thì không, và nó nện API suốt đêm ở màn hình treo tường.

**R6 — Không `useQuery` cho việc GHI.** Mọi POST/DELETE là `useMutation`. Nghe hiển nhiên nhưng
`/v1/scan` là POST mà "cảm giác" như đọc — vẫn phải là mutation vì nó tạo bản ghi.

### 4.2 Zustand — danh sách ĐÓNG

Chỉ được có **bốn** store. Muốn thêm cái thứ năm thì phải sửa tài liệu này trước và ghi rõ lý do.

| Store | Giữ gì | Vì sao không phải TanStack Query |
| --- | --- | --- |
| `useSessionStore` | `full_name`, `roles[]` của người đang đăng nhập | Đọc rất nhiều nơi (ẩn/hiện nút). Nạp một lần từ `/auth/login` hoặc `/auth/refresh` |
| `useStationStore` | `station` + `stationToken` của **THIẾT BỊ** | Đây là cấu hình của cái máy tính bảng, không phải của người. **Persist localStorage** — xem §7.3 |
| `useScanStore` | mã vừa quét, kết quả lần quét trước | Trạng thái UI thuần của màn quét |
| `useUiStore` | toast, modal đang mở, theme, cỡ chữ | UI thuần |

**Quy tắc chung cho Zustand:**

- **Cấm lưu bất cứ thứ gì lấy từ API** vào store (trừ `session` và `stationToken` ở trên — cả hai đều
  là *danh tính*, không phải *dữ liệu nghiệp vụ*).
- Selector phải **hẹp**: `useSessionStore(s => s.roles)`, không `useSessionStore()`. Lấy cả store là
  mọi thay đổi đều re-render.
- `persist` **chỉ** cho `useStationStore` và phần theme của `useUiStore`. Không persist session —
  quyền phải hỏi lại server mỗi lần mở app.
- Mỗi store một tệp trong `src/stores/`, tên `use<Tên>Store.ts`.

### 4.3 react-hook-form + zod

**R7 — Mọi form dùng RHF + zodResolver. Không `useState` cho ô nhập.**

**R8 — Zod schema phải khớp backend, đồng bộ HAI CHIỀU.** Backend đổi thì schema đổi theo, và ngược
lại. Bảng đối chiếu bắt buộc:

| Trường | Zod | Nguồn sự thật ở backend |
| --- | --- | --- |
| `mo_code` | `.regex(/^M\d{6}$/)` | `CHECK mo_code_format` |
| `quantity` | `.int().positive()` | `CHECK (quantity > 0)` |
| `pcs_per_box` | `.int().min(0)` | `CHECK (pcs_per_box >= 0)` · **0 = không đóng thùng** |
| `slot_hour` | `.int().min(0).max(23)` | `CHECK (slot_hour BETWEEN 0 AND 23)` |
| `headcount`, `target_qty`, `qty` | `.int().positive()` | ba số **bắt buộc** ở API |
| `boxes` | `.int().positive()` | `CHECK (boxes > 0)` |
| `qty_ok + qty_ng + qty_short` | **không kiểm ở FE** | trigger `production_balances` |

> **Vì sao dòng cuối không kiểm ở FE:** mục tiêu vòng nằm ở server và đổi theo vòng. Kiểm ở FE thì có
> hai luật, và luật FE sẽ sai trước. FE chỉ **hiện tổng sống** (`Σ 10.000 — khớp` / `Σ 9.800 — hụt
> 200`) cho người gõ thấy, rồi để server chặn.

**R9 — Lỗi từ server đổ vào form bằng `setError`,** không hiện toast rồi để form trống trơn. Người
vận hành phải thấy ô nào sai.

**R10 — Nút Submit `disabled` khi `isSubmitting`.** Đầu đọc QR và ngón tay đeo găng bấm đúp là chuyện
thường. Backend có `scan_dedupe` chống trùng 2 giây, nhưng đó là lưới cuối, không phải lớp đầu.

### 4.4 Axios

**R11 — Một client duy nhất** `src/services/axiosConfig.ts`:

- `withCredentials: true` — token nằm trong cookie **httpOnly**, FE không đọc được và **không được
  lưu vào localStorage**.
- Interceptor `401` → gọi `POST /v1/auth/refresh` **một lần** → thử lại request gốc. Refresh hỏng →
  xoá session, đá về `/login`.
- **Chống refresh dồn:** nhiều request 401 cùng lúc phải **dùng chung một** promise refresh, không
  gọi 5 lần. Backend **xoay vòng refresh token** và **thu hồi cả chuỗi khi phát hiện dùng lại** — gọi
  song song là tự đá mình ra khỏi phiên.

**R12 — Chuẩn hoá lỗi ở một chỗ.** Backend luôn trả `{ code, message }`:

```ts
export type ApiError = { code: string; message: string; status: number };
```

- **`message` là tiếng Việt viết sẵn cho người vận hành — hiện nguyên văn.** Cấm dịch lại, cấm ghép
  câu, cấm thay bằng "Có lỗi xảy ra".
- **`code` là thứ FE dùng để rẽ nhánh**, không phải `message` (message có thể sửa bất cứ lúc nào).

```ts
if (err.code === ERR.SKIP_STEP)  // → hiện màn "chưa xong trạm trước"
if (err.code === ERR.BOX_OVER_MADE) // → tô đỏ ô số thùng
```

Khai mã lỗi vào `src/constants/errorCodes.ts`, **chép từ**
`mes-backend/app/common/vocab/error_codes.py`. Không gõ chuỗi trần rải rác.

### 4.5 Next.js App Router

**R13 — Mặc định Server Component; thêm `"use client"` chỉ khi thật cần** (hook, state, sự kiện).
Trang MES hầu hết là client vì có polling và form — nhưng layout, khung tĩnh thì không.

**R14 — Route group theo TRẠM**, vì người dùng thuộc về một trạm cả ca:

```
src/app/
├─ (auth)/login/
├─ (station)/
│   ├─ scan/                 quét QR — màn dùng nhiều nhất
│   ├─ warehouse-out/        trạm 0
│   ├─ setup/                trạm 1
│   ├─ qc/                   trạm 2
│   ├─ waiting/              trạm 3 — Bàn team leader
│   ├─ production/           trạm 4 — chuyền · sản lượng giờ · đóng thùng
│   └─ warehouse-in/         trạm 5
├─ (planner)/
│   ├─ mos/                  tạo · import · submit · huỷ
│   └─ catalog/lines/        quản trị chuyền
└─ (board)/
    ├─ running/              bảng đang chạy — treo tường
    └─ mos/[code]/trace/     truy vết một MO
```

**R15 — Bộ lọc/tab/trang nằm ở `searchParams`,** không ở `useState`. F5 hoặc gửi link cho tổ trưởng
vẫn ra đúng màn đang xem.

---

## 5. Cấu trúc thư mục

```
src/
├─ app/                    routes (§4.5)
├─ components/
│   ├─ ui/                 nguyên thuỷ design-system — App*.tsx
│   ├─ common/             dùng lại toàn app: AppHeader, StationNav, EmptyState, ErrorState…
│   ├─ layouts/            StationLayout, BoardLayout, PlannerLayout
│   ├─ scan/               theo TÍNH NĂNG, tên trùng route group
│   ├─ production/
│   ├─ packing/
│   ├─ board/
│   └─ mo/
├─ hooks/                  mọi useQuery/useMutation — chia theo miền
│   ├─ board/  mo/  production/  packing/  scan/  auth/
│   └─ useDebounce.ts  useScanInput.ts …
├─ services/               *.service.ts + axiosConfig.ts + http.ts
├─ schemas/                zod, một tệp một miền
├─ stores/                 đúng 4 tệp (§4.2)
├─ constants/              queryKeys.ts · errorCodes.ts · stations.ts · roles.ts
├─ types/                  kiểu khớp response backend
├─ utils/                  format số/giờ, tính thùng…
└─ context/                QueryProvider · ToastProvider · ThemeProvider
```

**Quy tắc đặt tệp:** hỏi *"cái này có ý nghĩa ngoài tính năng của nó không?"*
Có → `components/common/`. Không → `components/<tính-năng>/`.
Nếu nó chỉ là nguyên thuỷ hình khối (nút, thẻ, ô nhập) → `components/ui/`.

---

## 6. Giao diện — phân tách, icon, PWA

### 6.1 Giới hạn cứng 200 dòng

Mỗi tệp `.ts`/`.tsx` **không quá 200 dòng**. Vượt thì tách theo thứ tự ưu tiên:

1. Tách **hook** — logic gọi API, tính toán, quản state → `src/hooks/`
2. Tách **helper** — format, quy đổi → `src/utils/`
3. Tách **component con** — khối JSX lặp hoặc độc lập
4. Cuối cùng mới tách theo "phần trên / phần dưới màn hình"

> Đây không phải luật thẩm mỹ. Tệp 600 dòng là tệp không ai dám sửa, và trong MES thì "không dám sửa"
> nghĩa là nghiệp vụ thay đổi mà code thì không.

### 6.2 Ba tầng component

| Tầng | Biết gì | KHÔNG được biết gì | Ví dụ |
| --- | --- | --- | --- |
| `ui/` | chỉ props | API, route, nghiệp vụ MES | `AppButton` `AppCard` `AppInput` `AppModal` `StatusPill` |
| `common/` | route, theme, session | API nghiệp vụ cụ thể | `AppHeader` `StationNav` `EmptyState` `ErrorState` `ConfirmDialog` |
| `<tính-năng>/` | gọi hook, biết nghiệp vụ | **không tự gọi axios** | `QueueTable` `LineRunCard` `HourlyForm` `BoxHourlyForm` |

**R16 — `ui/` không được import `hooks/` hay `services/`.** Vi phạm luật này là bước đầu của việc
không tái dùng được gì cả.

### 6.3 Bộ component phải có trước khi dựng màn hình

Dựng xong bảy cái này rồi mới làm màn — làm ngược thì mỗi màn đẻ một kiểu nút.

| Component | Dùng ở đâu |
| --- | --- |
| `AppButton` (`primary` `ghost` `danger`, `size="lg"` mặc định cho xưởng) | khắp nơi |
| `AppCard` · `AppInput` · `AppSelect` · `AppModal` | khắp nơi |
| `StatusPill` | map `MoStatus` · trạng thái chuyền · kết quả QC → màu + nhãn VI |
| `StationBadge` | số trạm + tên trạm, một nguồn duy nhất cho 6 trạm |
| `RoundBadge` | **`Vòng 2`** — bắt buộc trên mọi màn hiện số liệu (§1) |
| `QtyStat` | một con số lớn + nhãn nhỏ, dùng cho đạt/hỏng/thiếu/đã đóng |
| `EmptyState` · `ErrorState` | mọi bảng, mọi truy vấn |

**R17 — Không màn hình nào được tự chế trạng thái rỗng/lỗi.** Dùng `EmptyState`/`ErrorState`. Mỗi màn
một kiểu báo lỗi là cách nhanh nhất để người vận hành mất tin tưởng.

### 6.4 Typography & token — chép nguyên hệ từ `roomify-ui`

**Font.** Y hệt `roomify-ui/src/app/globals.css`:

```css
@import url('https://fonts.googleapis.com/css2?family=Google+Sans+Flex:opsz,wght@6..144,1..1000&display=swap');

@font-face {                          /* chép tệp từ roomify-ui/public/fonts/ */
  font-family: 'SVN-Gilroy';
  src: url('/fonts/SVN-Gilroy-SemiBold.otf') format('opentype');
  font-weight: 600; font-style: normal; font-display: swap;
}

:root {
  --font-heading: 'SVN-Gilroy', 'Google Sans Flex', system-ui, sans-serif;
  --font-sans:    'Google Sans Flex', system-ui, -apple-system, 'Segoe UI', sans-serif;
}
```

`body` dùng `var(--font-sans)`; `h1..h4` và `.font-heading` dùng `var(--font-heading)` kèm
`letter-spacing: -0.01em`.

**Thang cỡ chữ.** Giữ NGUYÊN tên token và NGUYÊN công thức `calc(… * var(--fs))`:

```css
:root {
  --fs: 1.15;                                  /* ← MES khác roomify, xem R29 */
  --text-display:  calc(40px   * var(--fs));
  --text-h1:       calc(32px   * var(--fs));
  --text-h2:       calc(26px   * var(--fs));
  --text-h3:       calc(21px   * var(--fs));
  --text-title:    calc(18px   * var(--fs));
  --text-body-lg:  calc(17px   * var(--fs));
  --text-body:     calc(15px   * var(--fs));
  --text-body-sm:  calc(13.5px * var(--fs));
  --text-caption:  calc(12px   * var(--fs));
  --text-label:    calc(13.5px * var(--fs));
  --text-button:   calc(15px   * var(--fs));
  --text-badge:    calc(12px   * var(--fs));
}
```

**R29 — MES đặt `--fs` mặc định là `1.15`, không phải `1`.**

Đây là chỗ duy nhất tôi lệch khỏi roomify, và lệch có lý do: thang gốc là cho **điện thoại cầm tay**
— `--text-body` 15px, `--text-caption` 12px. MES chạy trên **máy tính bảng gắn tường, người đeo găng,
xưởng chói**, và §1 đã chốt **chữ tối thiểu 16px**. Với `--fs: 1.15`:

| Token | roomify (`--fs:1`) | MES (`--fs:1.15`) |
| --- | ---: | ---: |
| `--text-body` | 15px | **17.3px** |
| `--text-body-sm` | 13.5px | 15.5px |
| `--text-caption` | 12px | 13.8px |
| `--text-h1` | 32px | 36.8px |

> **Vì sao chỉnh `--fs` chứ không sửa từng con số:** giữ nguyên thang thì **mọi component bê từ
> `roomify-ui` sang vẫn đúng tỉ lệ**, và sau này muốn to/nhỏ toàn app chỉ đổi một biến. Sửa 12 con số
> là tự tạo ra một hệ thứ hai phải bảo trì.

**R30 — `--fs` chỉnh được lúc chạy, 5 mức y như roomify** (`ThemeContext`):

```ts
export const FONT_SCALE_STEPS  = [0.9, 1, 1.15, 1.3, 1.5] as const;
export const FONT_SCALE_LABELS = ["90%", "100%", "115%", "130%", "150%"] as const;
// MES mặc định step 2 (1.15); roomify mặc định step 1 (1.0)
```

Lưu localStorage, có script chống FOUC trong `layout.tsx`. **Bảng treo tường nên để mức `1.3`–`1.5`** —
nhìn từ giữa xưởng.

**R32 — Theme có BA chế độ: `light` · `dark` · `system`** (y roomify), nhưng **mặc định là `dark`, không
phải `system`**. Máy tính bảng mới bóc hộp đang để chế độ sáng, mà màn này treo ở xưởng chói cả ca.

Chế độ `system` phải **nghe** `matchMedia("(prefers-color-scheme: light)")` chứ không chỉ đọc một lần
lúc mở app — máy để tự đổi sáng/tối theo giờ, đến chiều là lệch. Và **luật "sáng hay tối" trong script
chống FOUC ở `layout.tsx` phải khớp từng chữ với `ThemeProvider`**: lệch một chỗ là app nháy đúng một
nhịp mỗi lần mở, chỉ với người để `system` — loại lỗi không ai báo mà ai cũng thấy.

Nơi chỉnh: màn **`/account`** (`ThemeControls`). Vào từ khối người dùng ở đáy thanh bên (≥1280px), hoặc
nút tròn góc dưới phải (`AccountFab`, <1280px) vì tablet không có thanh bên.

**R34 — `font-mono` CHỈ dùng cho dữ liệu, không dùng cho chữ giao diện.** Mã lệnh, mã chuyền, mã lỗi,
ô nhập mã, và các cột số cần thẳng hàng — hết. Nhãn, tiêu đề mục, tên nav, badge đếm đều là chữ thường
của `--font-sans`. roomify-ui dùng đúng giới hạn này (mono chỉ cho `invoice._id`, `contract._id`), và
mono rải ra nhãn là thứ làm MES trông lệch hẳn khỏi roomify dù cùng bộ token.

Số thẳng hàng thì dùng `.tnum` (`font-variant-numeric: tabular-nums`) — nó ăn với cả font sans, không
cần đổi sang mono.

**R33 — Toast neo ở ĐẦU trang, không phải đáy.** Máy tính bảng dựng đứng trên bàn trạm thì mép dưới lọt
khỏi tầm mắt người đang đứng, mà họ vừa bấm nút xong là đang nhìn lên trên. Chừa `env(safe-area-inset-top)`
cho tai thỏ khi chạy toàn màn hình.

**Ánh xạ sang Tailwind** (`tailwind.config.ts`) — cỡ chữ **kèm luôn weight**, chép nguyên:

```ts
fontSize: {
  caption:   ["var(--text-caption)",  { fontWeight: "400" }],
  "body-sm": ["var(--text-body-sm)",  { fontWeight: "400" }],
  body:      ["var(--text-body)",     { fontWeight: "400" }],
  "body-lg": ["var(--text-body-lg)",  { fontWeight: "400" }],
  title:     ["var(--text-title)",    { fontWeight: "600" }],
  h3:        ["var(--text-h3)",       { fontWeight: "600" }],
  h2:        ["var(--text-h2)",       { fontWeight: "600" }],
  h1:        ["var(--text-h1)",       { fontWeight: "600" }],
  display:   ["var(--text-display)",  { fontWeight: "600" }],
  label:     ["var(--text-label)",    { fontWeight: "500" }],
  button:    ["var(--text-button)",   { fontWeight: "500" }],
  badge:     ["var(--text-badge)",    { fontWeight: "500" }],
},
fontFamily: { heading: ["var(--font-heading)"], sans: ["var(--font-sans)"] },
```

**R31 — Chỉ ba weight: 400 · 500 · 600. Cap `bold`/`extrabold`/`black` về 600.**

```ts
fontWeight: { normal: "400", medium: "500", semibold: "600",
              bold: "600", extrabold: "600", black: "600" },
```

Cap ở config chứ không chỉ "dặn nhau đừng dùng": ai gõ `font-bold` theo phản xạ vẫn ra 600, không phá
được hệ. `SVN-Gilroy` cũng chỉ có tệp SemiBold — để `font-bold` ra 700 là trình duyệt **tự bôi đậm
giả**, nét bệt và xấu hẳn.

**R32 — Cấm cỡ chữ và màu tuỳ ý.** Không `text-[15px]`, không `text-[#00E013]`, không `text-slate-400`.
Dùng `text-body` · `text-caption` · `text-fg-muted` … Cỡ chữ cứng **không nhân theo `--fs`**, nên nó
là đúng một chỗ mà nút chỉnh cỡ chữ bấm vào không ăn.

**Token còn lại** (giữ nguyên quy ước roomify):

- Bán kính bo: **một nguồn duy nhất** `rounded-field | rounded-card | rounded-pill`. Cấm
  `rounded-2xl`, `rounded-[22px]` trên card.
- Mặc định **phẳng**: phân tách bằng viền `border-line`, không đổ bóng. Shadow chỉ cho thứ thật sự
  nổi (thanh hành động ghim đáy).
- Màu qua token `bg`/`surface`/`surface-2`/`fg`/`fg-muted`/`line`… để dark mode tự đổi.

### 6.5 Icon — chỉ Phosphor

**R18 — Cấm SVG inline, và cấm import `@phosphor-icons/react` rải rác.** Mọi icon đi qua đúng một
tệp `src/components/common/PhosphorIcons.tsx`:

```tsx
"use client";
import { IconContext } from "@phosphor-icons/react";

export { QrCode, Package, Truck, CheckCircle, XCircle, Play, Pause,
         Clock, Warning, ArrowLeft, User, Gear /* … */ } from "@phosphor-icons/react";

/** Đặt weight/size mặc định một chỗ — bọc quanh app trong layout. */
export function IconProvider({ children }: { children: React.ReactNode }) {
  return (
    <IconContext.Provider value={{ size: 24, weight: "regular" }}>
      {children}
    </IconContext.Provider>
  );
}
```

Cần icon mới → thêm một dòng export ở đây, tra tên tại **phosphoricons.com**.

**Hai prop của Phosphor, hay gõ nhầm:**

| Muốn gì | Viết thế nào |
| --- | --- |
| Đổi độ đậm nét | `weight="regular / bold / fill / duotone"` |
| Đổi cỡ | `size={28}` **hoặc** `className="h-7 w-7"` — nhận cả hai |

**KHÔNG có prop `strokeWidth`.** Truyền vào thì **không báo lỗi mà cũng không có tác dụng** — icon vẫn
mảnh trong khi anh tưởng đã làm đậm. Đây là phản xạ tay quen từ bộ icon khác, để ý chỗ này.

**Riêng cho xưởng:** icon mặc định `size: 24`; icon trong nút thao tác chính dùng `size={28}` và
`weight="bold"` — người đeo găng nhìn từ xa, nét mảnh là không thấy.

### 6.6 PWA — cài lên máy tính bảng ở trạm

**Vì sao MES cần PWA, không phải để "cho hiện đại":**

| Lợi ích | Ý nghĩa ngoài xưởng |
| --- | --- |
| Cài ra màn hình chính | Người ở trạm bấm một icon, không phải gõ URL hay tìm tab |
| `display: standalone` | **Không còn thanh địa chỉ và nút Back của trình duyệt** — bớt hẳn một lớp bấm nhầm |
| `orientation: landscape` | Máy tính bảng ở trạm và màn treo tường đều nằm ngang |
| Service worker | Điều kiện để trình duyệt cho phép "Cài ứng dụng" |

**R24 — Dùng service worker VIẾT TAY, không dùng `next-pwa`.**
`next-pwa`/Workbox mặc định cache rất hăng, mà **MES thì mọi con số đều là số sống**. Cache nhầm một
hàng đợi là người ở trạm nhìn thấy lệnh đã bị trạm khác lấy mất. Một tệp 60 dòng mà mình đọc hết còn
an toàn hơn một thư viện mình không biết nó cache gì. `roomify-ui` cũng đang làm đúng vậy.

**R25 — Service worker TUYỆT ĐỐI không cache `/v1/*`.**

```js
// public/sw.js
self.addEventListener("install",  () => self.skipWaiting());
self.addEventListener("activate", (e) => e.waitUntil(self.clients.claim()));

self.addEventListener("fetch", (event) => {
  // Chỉ đụng tới điều hướng trang. API đi thẳng, KHÔNG qua tay service worker —
  // dữ liệu MES là số sống, cache một hàng đợi là gây sai việc ngoài xưởng.
  if (event.request.mode !== "navigate") return;
  event.respondWith(fetch(event.request));
});
```

> Handler `fetch` này **gần như không làm gì** — nhưng phải có, vì trình duyệt đòi có nó mới cho cài
> ứng dụng. Đừng thấy nó rỗng rồi xoá đi.

**Cần những gì:**

```
public/manifest.json          name · short_name · start_url · display · orientation · icons
public/sw.js                  60 dòng ở trên
public/icon-192x192.png       cho Android
public/icon-512x512.png
public/icon-maskable-512.png  purpose: "maskable" — Android bo góc icon
public/apple-touch-icon.png   iOS BỎ QUA manifest, chỉ đọc thẻ này
scripts/generate-pwa-icons.mjs  sinh cả bộ từ 1 file gốc bằng sharp
src/app/layout.tsx            metadata.manifest + đăng ký sw + IconProvider
src/hooks/usePwaInstall.ts    bắt beforeinstallprompt → nút "Cài ứng dụng"
src/components/common/PwaInstallPrompt.tsx
```

`manifest.json` cho MES:

```json
{
  "id": "/",
  "name": "MES | Amphenol RF",
  "short_name": "MES",
  "start_url": "/scan",
  "scope": "/",
  "display": "standalone",
  "orientation": "landscape",
  "lang": "vi",
  "background_color": "#0b0f14",
  "theme_color": "#0b0f14",
  "icons": [
    { "src": "/icon-192x192.png",      "sizes": "192x192", "type": "image/png", "purpose": "any" },
    { "src": "/icon-512x512.png",      "sizes": "512x512", "type": "image/png", "purpose": "any" },
    { "src": "/icon-maskable-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable" }
  ]
}
```

**R26 — `start_url` là `/scan`, không phải `/`.** Máy tính bảng ở trạm mở lên là để quét. Bắt người ta
đi qua một trang chủ rồi mới tới ô quét là thêm một chạm, mỗi ca vài trăm lần.

**R27 — iOS không đọc `manifest.json`.** Icon màn hình chính của iPad chỉ lấy từ
`<link rel="apple-touch-icon">`, và **phải là PNG thật**, không SVG, không có alpha ở viền.

**R28 — Màn hình trạm phải KHÔNG ngủ.** Máy tính bảng tắt màn giữa ca là người ta phải cởi găng để
mở khoá. Dùng **Screen Wake Lock API** ở màn `/scan` và bảng treo tường:

```ts
// src/hooks/useWakeLock.ts — xin lại khi tab được focus, vì hệ điều hành tự thu hồi
const s = await navigator.wakeLock?.request("screen");
```

Trình duyệt nào không hỗ trợ thì thôi, **không chặn app** — đây là tiện nghi, không phải điều kiện.

**Web Push: CHƯA làm.** `roomify-ui` có `web-push` + `usePushNotification`, nhưng backend MES **chưa
có endpoint đăng ký subscription nào**. Đừng chép phần push sang. Khi nào cần báo "MO về hàng đợi của
bạn" thì làm backend trước.

---

## 7. Hợp đồng với backend — bốn chỗ dễ làm sai

### 7.1 Đăng nhập & cookie

```
POST /v1/auth/login    { emp_code, pin }  → SessionOut { full_name, roles[] } + 2 cookie httpOnly
POST /v1/auth/refresh                     → SessionOut  (xoay vòng refresh token)
POST /v1/auth/logout                      → OkOut       (thu hồi thật, không chỉ xoá cookie)
```

| Cookie | Path | Ý nghĩa |
| --- | --- | --- |
| `mes_access` | `/` | đi kèm mọi request |
| `mes_refresh` | `/v1/auth` | **chỉ** gửi tới nhóm auth — ít lộ hơn hẳn |

**R19 — FE và BE phải CÙNG SITE** (qua reverse proxy). Backend đang đặt `samesite=lax`; để khác
origin thì phải `samesite=none` + HTTPS, và lúc đó **mất lá chắn CSRF của trình duyệt** → cần thêm
CSRF token, việc này backend **chưa làm**. Đừng tự ý đổi origin rồi mới báo.

**R20 — Logout phải gọi API.** Chỉ `router.push("/login")` là phiên vẫn sống ở server.

### 7.2 Quyền hiển thị

`roles[]` từ `SessionOut`. Chép bảng quyền §9b vào `src/constants/roles.ts` và viết đúng **một** hàm:

```ts
permissionFor(roles: string[], step: number): "FULL" | "VIEW" | null
```

**R21 — Ẩn/hiện theo quyền là để đỡ bấm nhầm, KHÔNG phải bảo mật.** Backend vẫn chặn bằng
`require_step`. Đừng bao giờ nghĩ "FE ẩn rồi thì khỏi cần".

Ba ngoại lệ hay quên, chép thẳng từ §9b:
- **Bàn team leader có FULL quyền trạm 4**, kể cả đóng thùng.
- **Mọi phòng ban đều VIEW được trạm 4** và Bảng đang chạy.
- **Kho xuất (0) và Kho nhập (5) là hai phòng ban riêng** — không gộp.

### 7.3 Station token — thứ đặc biệt nhất của MES

`POST /v1/scan` cần header **`X-Station-Token`**, và đây **không phải** token người dùng.

> BRD §1b.3: *"mã QR chỉ nói MO nào, không nói bước nào"* — bước lấy từ **THIẾT BỊ**. Để client tự
> khai trạm trong body thì một máy giả được mọi trạm.

**R22 —**
- Nạp một lần khi cấu hình máy tính bảng: `POST /v1/auth/station-token` → `{ station, token }`.
- Lưu ở `useStationStore` có `persist` localStorage — **đây là ngoại lệ duy nhất** của luật "không
  lưu token ở localStorage", vì nó gắn với cái máy đặt cố định ở trạm, không phải với người.
- Axios gắn header này **chỉ cho `/scan`**, không gắn bừa vào mọi request.
- Máy chưa cấu hình trạm → màn quét hiện màn "Thiết bị chưa đăng ký trạm", không hiện ô quét.

### 7.4 Đơn vị — PCS vs THÙNG

**R23 — Tiến độ MO luôn tính bằng PCS. FE không bao giờ nhân/chia thùng để ra tiến độ.**

| Việc | Đơn vị | Ghi chú |
| --- | --- | --- |
| `quantity`, `qty_ok/ng/short`, `qty_packed`, tiến độ | **PCS** | |
| Ghi theo giờ ở đóng thùng | **THÙNG ĐẦY** | `POST /packing/{code}/hourly` |
| `Kết thúc đóng thùng` | **PCS** | gồm cả **thùng lẻ cuối** |

- Endpoint thùng trả sẵn `packed_pcs`, `made_pcs`, **`le_pcs`** — **dùng số server trả, đừng tự tính
  lại**. Hai nơi tính là hai nơi lệch.
- **`le_pcs` phải hiện kèm chữ "chưa đủ thùng, KHÔNG phải hàng thiếu".** Đây là chỗ người vận hành
  hiểu nhầm nhiều nhất và hiểu nhầm thì họ đi báo thiếu hàng.
- Sản lượng giờ: nhập `headcount` · `target_qty` · `qty`. **`Đạt %` và `Năng suất` FE tự tính để
  HIỆN, không có ô nhập.**

---

## 8. Màn hình ↔ API

### 8.1 Mô hình phải nắm trước khi đọc bảng

**`POST /scan` là thao tác NHẬN của CẢ SÁU TRẠM.** Endpoint riêng của từng trạm là *việc làm ở trạm
đó*, không phải việc nhận.

```
Quét QR  →  POST /scan        → trạm hiện tại NHẬN lệnh, và trạm TRƯỚC tự đóng
Làm việc →  endpoint của trạm → bàn giao · kết quả QC · chạy chuyền · chốt sổ · nhập kho
```

> **Trạm 1 (Setup máy) và trạm 3 (Bàn team leader) KHÔNG có endpoint riêng — và đó là đúng.**
> BRD §4: *"không có nút Complete riêng, Step N Complete khi Step N+1 nhận."* Hai trạm này **không
> sinh dữ liệu gì ngoài giờ giấc**; giờ giấc thì đã nằm trong `mo_step` do chính lần quét ghi. Setup
> xong không bấm gì cả — QC quét là `STEP1` tự đóng.
>
> Đừng đi tìm `POST /setup/{code}`. Không có, và thêm vào là thêm một nút không có việc để làm.

### 8.2 Bảng đầy đủ — sáu trạm

| Trạm | Màn hình | Hàng đợi | Nhận lệnh | Việc của trạm |
| --- | --- | --- | --- | --- |
| **0** Kho xuất | `/warehouse-out` | `GET /board/queue/0` | `POST /scan` | `POST /warehouse-out/{code}/handover`<br>`POST /warehouse-out/handover-batch` |
| **1** Setup máy | `/setup` | `GET /board/queue/1` | `POST /scan` | **không có** — xem §8.1 |
| **2** QC | `/qc` | `GET /board/queue/2` | `POST /scan` | `POST /qc/{code}` |
| **3** Bàn team leader | `/waiting` | `GET /board/queue/3` | `POST /scan` | **không có** — xem §8.1 |
| **4** Sản xuất | `/production` | `GET /board/queue/4` | `POST /scan` | `POST /lines/{code}/assign`<br>`POST /lines/{code}/start`<br>`POST /lines/{code}/hold`<br>`POST /production/{code}/close`<br>`POST /hourly/{code}` |
| **4** Đóng thùng *(song song)* | `/production` (panel) | — | — | `POST /packing/{code}/start`<br>`POST /packing/{code}/hourly`<br>`POST /packing/{code}/finish` |
| **5** Kho nhập | `/warehouse-in` | `GET /board/queue/5` | `POST /scan` | `POST /warehouse-in/{code}/complete` |

**Mỗi trạm có HAI danh sách, không phải một.** `GET /board/queue/{station}` là việc **chưa ai nhận**;
`GET /board/at/{station}` là việc **đang trong tay trạm** (đã quét nhận, chưa trạm sau lấy đi). Bản đầu
của FE chỉ có cái thứ nhất, nên quét xong lệnh biến mất khỏi màn và không còn dấu vết nào cho thấy nó
đang nằm ở đây — nhìn vào không đoán ra luồng chạy thế nào.

Bước chỉ đóng khi trạm SAU quét nhận, nên danh sách thứ hai **không có nút "xong"**. Cột duy nhất đáng
xem ở đó là thời gian giữ.

**Màn hình của trạm 1 và 3 có gì?** Hàng đợi + ô quét + đồng hồ bước, hết. Chúng vẫn là màn thật và
vẫn cần thiết — người ở Setup phải thấy lệnh nào đang chờ mình và đã nhận lúc mấy giờ.

### 8.3 Ngoài trạm

| Màn | Method | Endpoint |
| --- | --- | --- |
| Đăng nhập | POST | `/auth/login` · `/auth/refresh` · `/auth/logout` |
| Cấu hình thiết bị | POST | `/auth/station-token?station=<n>` — **`station` là QUERY param, không phải body**, và endpoint chỉ mở cho `PLANNER` |
| Tài khoản · giao diện · cỡ chữ | — | không gọi API. Tên và quyền lấy từ `useSessionStore`; theme/cỡ chữ ở `useUiStore` (R32) |
| Kế hoạch — tạo/nhập/chốt/huỷ | POST | `/mos` · `/mos/bulk` · `/mos/{code}/submit` · `/mos/{code}/cancel` |
| Chi tiết MO | GET | `/mos/{code}` |
| Bảng đang chạy *(treo tường)* | GET | `/board/running` · `/board/counts` |
| Truy vết MO | GET | `/mos/{code}/trace` |
| Danh mục chuyền | GET/POST/DELETE | `/lines` · `/lines/{code}` |
| Danh mục lý do | GET | `/reasons` |

**Lưu ý kiểu dữ liệu:** `/board/queue/{station}`, `/board/running`, `/mos/{code}/trace` **chưa gắn
`response_model`** ở backend (cố ý — chúng trả thêm field tuỳ trạm, gắn vào là bị lọc mất mà không
báo lỗi gì). Khai type ở `src/types/` theo response thật, và **kiểm lại khi backend đổi** — không có
gì tự canh hộ.

---

## 9. Lộ trình

| Giai đoạn | Làm gì | Xong khi nào |
| --- | --- | --- |
| **0 — Nền** | Dựng dự án, **font + thang chữ §6.4** (chép `globals.css`, chép `public/fonts/`), Tailwind token, `QueryProvider`, axios + interceptor refresh, `errorCodes.ts`, `queryKeys.ts`, 4 store | `pnpm build` sạch · login thật chạy được |
| **0b — PWA** | `manifest.json` · `sw.js` · bộ icon (`generate-pwa-icons.mjs`) · `usePwaInstall` · `useWakeLock` | **Cài được lên iPad thật**, mở ra thẳng `/scan`, không thanh địa chỉ |
| **1 — Bộ component** | 7 component ở §6.3 + `PhosphorIcons.tsx` + `IconProvider` + `EmptyState`/`ErrorState` | Có trang `/dev/kit` xem đủ mọi biến thể |
| **2 — Quét + một trạm** | Màn `/scan` hoàn chỉnh + trạm 0 (Kho xuất) | Quét QR thật bằng đầu đọc chạy được từ đầu tới bàn giao |
| **3 — Sáu trạm** | Trạm 1→5, dùng lại khung của giai đoạn 2 | Đi hết một vòng MO trên UI |
| **4 — Trạm 4 đầy đủ** | Chuyền · chốt sổ 3 số · sản lượng giờ (3 số) · đóng thùng theo giờ | Chạy đúng kịch bản `3.000 pcs · 800/thùng` |
| **5 — Kế hoạch & Bảng** | Tạo/import MO · bảng đang chạy · truy vết | Bảng treo tường tự cập nhật 10s |
| **6 — Danh mục & hoàn thiện** | Quản trị chuyền · lý do · phân quyền hiển thị · a11y | Rà theo §10 |

> **Giai đoạn 2 là giai đoạn quan trọng nhất.** Làm xong một trạm cho thật đúng rồi nhân bản, đừng làm
> sáu trạm cùng lúc ở mức 70%.

---

## 10. Xong là xong — checklist trước khi bàn giao mỗi màn

```
[ ] pnpm lint && pnpm build sạch 100%
[ ] Không tệp nào > 200 dòng
[ ] Không fetch trong component — mọi API đi qua hook
[ ] Query key lấy từ factory · mutation có invalidate đúng bảng §4.1 R3
[ ] Không có dữ liệu API nào nằm trong Zustand
[ ] Form dùng RHF + zod · schema khớp bảng §4.3 R8
[ ] Lỗi hiện `message` nguyên văn từ server · rẽ nhánh bằng `code`
[ ] Có EmptyState và ErrorState
[ ] Màn hiện số liệu có RoundBadge
[ ] Vùng chạm ≥ 56px · chữ ≥ 16px
[ ] Không SVG inline · icon import từ `PhosphorIcons.tsx` · không `strokeWidth`
[ ] Không hardcode màu/px — dùng token `text-body`/`text-caption`/`text-fg-muted`…
[ ] Không `font-bold` mong ra 700 — hệ cap ở 600 (R31)
[ ] Bấm nút chỉnh cỡ chữ (`--fs`) thì MỌI chữ trên màn phải to/nhỏ theo
[ ] Service worker không chạm `/v1/*`
[ ] Thử với bàn phím + đầu đọc QR, không chỉ chuột
```

---

## 11. Điều tôi CHƯA quyết — cần chốt trước giai đoạn 0

| Câu hỏi | Vì sao phải chốt sớm |
| --- | --- |
| FE và BE **cùng site** qua reverse proxy? | Quyết định cookie `samesite` và có cần CSRF token không (§7.1 R19) |
| Máy tính bảng ở trạm dùng **một tài khoản chung** hay mỗi người một tài khoản? | Đổi hẳn luồng đăng nhập: tài khoản chung thì cần màn "chọn người" mỗi thao tác để `closed_by` còn đúng |
| Bảng treo tường có cần **chạy không cần đăng nhập** không? | Nếu có thì cần một vai chỉ-xem, backend chưa có |
| Ngoài xưởng có **wifi chập chờn** không? | Nếu có thì phải tính hàng đợi offline cho `/scan` — việc lớn, phải biết trước |

Bốn câu này đều thuộc loại *trả lời sai thì phải viết lại nhiều màn*, nên chốt trước khi gõ code.
