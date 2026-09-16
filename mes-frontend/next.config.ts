import type { NextConfig } from "next";

/**
 * FE và BE chạy CÙNG ORIGIN qua rewrite (FE-PLAN R19).
 *
 * Backend đặt cookie `samesite=lax`, nên gọi thẳng `localhost:8000` từ
 * `localhost:3000` là trình duyệt KHÔNG gửi cookie đi — đăng nhập xong vẫn 403.
 * Proxy qua chính Next thì mọi thứ là same-site và không cần CSRF token.
 */
const BACKEND = process.env.BACKEND_ORIGIN ?? "http://127.0.0.1:8000";

const SCRIPT = process.env.npm_lifecycle_event;

const nextConfig: NextConfig = {
  distDir: SCRIPT === "build" || SCRIPT === "start" ? ".next-build" : ".next",
  async rewrites() {
    return [{ source: "/v1/:path*", destination: `${BACKEND}/v1/:path*` }];
  },
};

export default nextConfig;
