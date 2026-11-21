# MES Frontend

Giao diện vận hành hệ thống MES cho nhà máy sản xuất. Xây dựng bằng Next.js 15 (App Router), React 19, TailwindCSS và TanStack Query.

## 5 Trạm sản xuất liên tục (0..4)

| Trạm | Tên màn hình | Đường dẫn | Thao tác chính |
|---|---|---|---|
| **0** | **Lấy nguyên liệu** | `/warehouse-out` | Quét nhận lệnh, Xem phiếu, Bàn giao xuống Setup (kèm popup ghi chú `HandoverModal`) |
| **1** | **Setup máy** | `/setup` | Hàng đợi Setup (hiển thị thẻ lưu ý dặn dò từ Kho), Quét nhận gá máy |
| **2** | **Team Leader** | `/waiting` | Bàn điều phối, nhận lệnh thiếu số hoặc sự cố quay về từ Kho nhập |
| **3** | **Sản xuất** | `/production` | Chọn line chạy lệnh, ghi sản lượng giờ, dừng chuyền, đóng thùng song song, chốt ca |
| **4** | **Kho nhập** | `/warehouse-in` | Quét nhận hàng thành phẩm, xác nhận nhập kho theo số thùng |

### Các màn hình quản trị & hỗ trợ:
* `/mos`: Lập kế hoạch, tạo lẻ, nhập danh sách MO từ Excel, submit lệnh.
* `/running`: Bảng Kanban trực quan hoá tiến độ thời gian thực cho toàn xưởng.
* `/reports`: Báo cáo sản lượng, KPI, hiệu suất chuyền.
* `/scan`: Màn quét mã vạch / QR dùng chung cho thiết bị đầu đọc ở trạm.

## Chạy Local

1. Cài đặt thư viện:
```bash
pnpm install
```

2. Cấu hình biến môi trường (`.env`):
```env
BACKEND_ORIGIN=https://mes-backend-adts.onrender.com
# hoặc khi chạy backend local:
# BACKEND_ORIGIN=http://127.0.0.1:8000
```
*(Next.js tự động rewrite `/v1/*` sang `BACKEND_ORIGIN` để giải quyết vấn đề CORS & Cookie SameSite).*

3. Khởi chạy:
```bash
pnpm dev
```
Truy cập: [http://localhost:3000](http://localhost:3000)

4. Kiểm tra TypeScript & Build:
```bash
pnpm tsc --noEmit
pnpm build
```
