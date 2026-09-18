import type { NextConfig } from "next";

/**
 * FE và BE chạy CÙNG ORIGIN qua rewrite (FE-PLAN R19).
 *
 * Backend đặt cookie `samesite=lax`, nên gọi thẳng `localhost:8000` từ
 * `localhost:3000` là trình duyệt KHÔNG gửi cookie đi — đăng nhập xong vẫn 403.
 * Proxy qua chính Next thì mọi thứ là same-site và không cần CSRF token.
 */
/* `||` chứ không `??`: bảng điều khiển của nhà cung cấp (Render…) đặt biến thành
   CHUỖI RỖNG khi người triển khai bỏ trống ô nhập. `??` chỉ rơi về mặc định khi
   biến là null/undefined, nên chuỗi rỗng lọt qua và đích rewrite thành "/v1/:path*"
   — trang tự chuyển tiếp vào chính nó, không có lỗi nào được in ra.

   Thiếu lược đồ thì thêm https: có bảng điều khiển phát địa chỉ dạng `host:port`. */
const RAW = process.env.BACKEND_ORIGIN?.trim();
const BACKEND = !RAW
  ? "http://127.0.0.1:8000"
  : /^https?:\/\//.test(RAW)
    ? RAW
    : `https://${RAW}`;

const SCRIPT = process.env.npm_lifecycle_event;

const nextConfig: NextConfig = {
  distDir: SCRIPT === "build" || SCRIPT === "start" ? ".next-build" : ".next",
  async rewrites() {
    return [{ source: "/v1/:path*", destination: `${BACKEND}/v1/:path*` }];
  },
};

export default nextConfig;
