# Triển khai lên Render — FE + BE + Postgres từ một kho

> Viết cho người triển khai hệ thống, không phải cho người viết code: bạn cần biết
> bấm gì ở đâu và vì sao, không cần đọc mã nguồn.
>
> Bản thiết kế: [`render.yaml`](../render.yaml) ở gốc kho.

---

## 1. Hình dạng

Một kho trên GitHub, Render dựng ra **ba thứ**:

| Tên | Là gì | Thư mục gốc |
| --- | --- | --- |
| `mes-db` | Postgres có quản | — |
| `mes-backend` | Docker, FastAPI | `mes-backend/` |
| `mes-frontend` | Node, Next.js | `mes-frontend/` |

Trình duyệt **chỉ nói chuyện với `mes-frontend`**. Mọi lời gọi `/v1/*` được máy chủ
Next chuyển tiếp sang backend (`rewrites` trong `next.config.ts`).

```
trình duyệt ──► mes-frontend ──► mes-backend ──► mes-db
             (một origin duy nhất)
```

**Đây là chỗ mấu chốt, không phải chi tiết kỹ thuật vụn.** Token đăng nhập nằm trong
cookie `httpOnly` với `samesite=lax`. Nếu trình duyệt phải gọi thẳng sang một tên miền
khác, trình duyệt **không gửi cookie đó đi** — đăng nhập xong vẫn bị từ chối. Cách
chữa duy nhất khác là hạ xuống `samesite=none`, mà làm vậy là vứt lá chắn CSRF của
trình duyệt trong khi **CSRF token chưa có trong mã nguồn**.

Nên: đừng trỏ frontend thẳng vào backend bằng URL tuyệt đối, và đừng đổi
`MES_COOKIE_SAMESITE`.

---

## 2. Trước khi bắt đầu

- Kho đã ở trên GitHub và Render có quyền đọc.
- `mes-backend/.env` **không** lên git (`.gitignore` đã chặn). Mọi bí mật ở máy thật
  đặt bằng biến môi trường trong bảng điều khiển Render.

---

## 3. Dựng lần đầu

**Bước 1 — tạo Blueprint.** Trong Render: *New → Blueprint*, chọn kho này. Render đọc
`render.yaml` và dựng cả ba. Nó sẽ hỏi hai biến để trống, cứ bỏ qua, điền ở bước 3.

**Bước 2 — chờ `mes-backend` xanh.** Mở log của nó, phải thấy đúng ba dòng này:

```
[entrypoint] alembic upgrade head
[entrypoint] uvicorn 0.0.0.0:10000
... "msg": "Kết nối CSDL OK — ..."
```

Migration chạy ngay trong lúc khởi động, bạn không phải làm gì thêm. Chép URL của
service, dạng `https://mes-backend-xxxx.onrender.com`.

**Bước 3 — điền `BACKEND_ORIGIN` cho `mes-frontend`.** Vào *mes-frontend → Environment*,
đặt `BACKEND_ORIGIN` bằng URL vừa chép. Lưu, service tự dựng lại.

Hậu tố `xxxx` do Render sinh ngẫu nhiên nên không thể ghi sẵn trong `render.yaml` —
đây là lý do duy nhất phải điền tay.

**Bước 4 — thử.** Mở URL của `mes-frontend`, đăng nhập bằng `NV001` / PIN `1234`.

Không phải tạo tài khoản: migration `0002_seed` vốn dựng sẵn 14 chuyền, danh mục lý
do, và tám tài khoản (`NV001` điều độ, `NV010`–`NV070` cho sáu trạm). Đó là **dữ liệu
hệ thống**, thiếu nó thì không trạm nào quét được — nên nó nằm trong migration chứ
không phải script chạy tay.

Muốn thêm lệnh sản xuất mẫu để xem màn hình có số: mở *mes-backend → Shell*, chạy
`python tools/seed_demo.py`. Mã lệnh mẫu đều bắt đầu bằng `M2` nên gỡ sạch được bằng
`--wipe`, không đụng lệnh thật.

---

## 3b. ĐỔI PIN TRƯỚC KHI GIAO CHO XƯỞNG

**Tám tài khoản kể trên đều dùng chung PIN `1234`, và chúng được tạo tự động ở mọi
lần triển khai.** Chính file migration cũng ghi `ĐỔI TRƯỚC KHI CHẠY THẬT`.

Nghĩa là ngay khi `mes-backend` xanh, bất kỳ ai biết URL đều đăng nhập được bằng
`NV001` / `1234` và có **toàn quyền vai điều độ** — tạo lệnh, huỷ lệnh, mở mọi trạm.

Trong lúc chỉ đang thử thì không sao. Trước khi xưởng dùng thật, phải làm xong hai việc:

1. Đổi PIN của cả tám tài khoản (hoặc xoá những tài khoản không dùng).
2. Cân nhắc khoá backend lại — xem §8.

Đây là việc của người triển khai, mã nguồn không tự làm hộ được.

---

## 4. Danh sách biến môi trường

`render.yaml` lo gần hết. Chỉ hai dòng cần người:

| Biến | Service | Ai đặt |
| --- | --- | --- |
| `BACKEND_ORIGIN` | mes-frontend | **Bạn**, ở bước 3 |
| `MES_CORS_ORIGINS` | mes-backend | Bỏ trống — xem dưới |
| `MES_DATABASE_URL` | mes-backend | Render tự nối từ `mes-db` |
| `MES_JWT_SECRET` | mes-backend | Render tự sinh, giữ nguyên mãi |

`MES_CORS_ORIGINS` để trống là đúng: CORS chỉ áp cho trình duyệt, mà trình duyệt
không bao giờ gọi thẳng vào backend trong sơ đồ này. Chỉ điền nếu bạn cố ý mở cho
một trang khác gọi vào.

---

## 5. Ba cái bẫy đã gỡ sẵn trong mã nguồn

Ghi lại để sau này ai sửa còn biết vì sao chúng ở đó.

**Chuỗi kết nối CSDL.** Render phát `postgres://…`. SQLAlchemy 2.0 đã **bỏ hẳn** lược
đồ đó, còn `postgresql://` trần thì nó đi tìm `psycopg2` — thứ không có trong
`pyproject.toml`. Cả hai đều gãy lúc khởi động. Nên `DatabaseSettings` trong
[`app/common/config.py`](../mes-backend/app/common/config.py) tự ghi driver `+psycopg`
vào. Nhờ đó nối thẳng từ `render.yaml` được, không phải chép tay.

**Cổng.** Render cấp cổng qua `$PORT` và **đổi theo mỗi lần triển khai**. Đóng cứng
`8000` thì bộ cân bằng tải gọi vào cổng không ai nghe và service bị coi là chết.
`docker-entrypoint.sh` đọc `$PORT`.

**Thư mục dựng của Next.** `next.config.ts` chọn thư mục theo biến `npm_lifecycle_event`,
nên lệnh **bắt buộc** đi qua script của npm:

| | |
| --- | --- |
| ✅ | `pnpm build` · `pnpm start` |
| ❌ | `next build` · `next start` trần |

Gọi trần thì build ghi một chỗ, start tìm một chỗ khác, và lỗi báo ra là
`Cannot find module for page: /login` — không nói một chữ nào về nguyên nhân thật.
`render.yaml` đã đặt đúng; đừng sửa hai dòng đó.

---

## 6. Một worker — cố ý, đừng tăng bừa

Backend chạy **một tiến trình uvicorn**, không phải `gunicorn -w 4` như
`docker-compose.yml`. Hai thứ phụ thuộc vào điều đó:

**Migration chạy trong entrypoint.** An toàn vì chỉ một tiến trình gọi
`alembic upgrade head`. Nhiều worker cùng gọi là giành nhau bảng `alembic_version` —
BE-PLAN §10 cấm.

**Bộ nhớ đệm đọc đúng tuyệt đối.** `app/common/read_cache.py` giữ đệm **trong bộ nhớ
của tiến trình**. Ghi xong thì nó nâng số phiên bản để đệm cũ hết hiệu lực ngay. Một
tiến trình thì số phiên bản là duy nhất, nên người vừa quét nhận xong nhìn hàng đợi
là thấy đúng liền.

Nhiều tiến trình thì **không**: worker A nhận cú quét và nâng phiên bản của riêng A;
B, C, D vẫn phát số cũ cho tới khi hết hạn 5 giây. Người vận hành thấy lệnh mình vừa
quét vẫn nằm trong hàng đợi và sẽ quét lại lần hai.

Một tiến trình vẫn chịu được tải của xưởng: endpoint đồng bộ của FastAPI chạy trong
một bể luồng, và `read_cache` đã cắt phần lớn truy vấn `/board/*` rồi.

**Nếu thật sự cần tăng worker hoặc tăng số bản sao**, phải làm đủ ba việc, không được
làm nửa vời:

1. Bỏ dòng `alembic upgrade head` khỏi `docker-entrypoint.sh`, đưa migration ra một
   bước chạy trước khi triển khai.
2. Nâng `MES_DATABASE_POOL_SIZE` / `MES_DATABASE_MAX_OVERFLOW` cho khớp trần kết nối
   của Postgres — nhớ nhân với số worker.
3. Chuyển `read_cache` sang chỗ dùng chung (Redis), hoặc chấp nhận 5 giây lệch.

---

## 7. Gói free dùng để thử, KHÔNG dùng cho xưởng

`render.yaml` đặt `plan: free` cho cả ba để dựng được trên mọi tài khoản. Trước khi
giao cho xưởng dùng thật, cân nhắc:

- **Service free ngủ khi không ai gọi**, và lần gọi kế tiếp phải chờ nó thức dậy.
  Người đứng máy quét QR mà chờ gần một phút thì họ sẽ bỏ, ghi tay, và sổ sai.
- **Postgres free có thời hạn giữ dữ liệu.** Hãy tự kiểm chính sách hiện hành bên
  Render — họ đổi theo thời gian. Mất CSDL sản xuất là mất toàn bộ sổ.
- Gói free không có bản sao lưu tự động.

Nâng gói thì sửa `plan:` trong `render.yaml`, không phải dựng lại.

---

## 8. Muốn giấu hẳn backend

Mặc định `mes-backend` là service công khai — ai biết URL đều gọi được API (vẫn phải
đăng nhập mới làm được gì). Đổi `type: web` thành `type: pserv` là nó không còn URL
công khai, chỉ `mes-frontend` gọi được qua mạng nội bộ.

Đánh đổi: `/docs` cũng không vào được từ ngoài, và Private Service không có ở mọi gói.
Nên để công khai lúc mới dựng — có `/healthz` và `/docs` để dò thì tìm lỗi nhanh hơn
nhiều — rồi đóng lại sau khi chạy ổn.
