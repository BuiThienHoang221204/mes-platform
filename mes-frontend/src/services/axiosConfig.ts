import axios, { AxiosError, AxiosRequestConfig } from "axios";
import type { ApiError } from "@/types/api";

/**
 * R11 — MỘT client duy nhất.
 *
 * `baseURL` là đường dẫn TƯƠNG ĐỐI: `next.config.ts` rewrite `/v1/*` sang
 * backend, nên trình duyệt thấy cùng origin và cookie `samesite=lax` đi được.
 */
export const apiClient = axios.create({
  baseURL: "/v1",
  withCredentials: true,
  headers: { "Content-Type": "application/json" },
});

/** Đổi lỗi axios thành hình dạng của backend. Chỗ DUY NHẤT làm việc này (R12). */
export function toApiError(err: unknown): ApiError {
  const ax = err as AxiosError<{ code?: string; message?: string }>;
  const status = ax?.response?.status ?? 0;
  const data = ax?.response?.data;
  if (data?.code && data?.message) return { code: data.code, message: data.message, status };
  if (status === 0) return { code: "NETWORK", message: "Mất kết nối tới máy chủ. Kiểm tra mạng rồi thử lại.", status };
  return { code: "DB", message: "Máy chủ gặp sự cố. Báo kỹ thuật kèm giờ xảy ra.", status };
}

/* ── 401 → refresh MỘT LẦN, dùng chung một promise ──────────────────────────
   Backend XOAY VÒNG refresh token và THU HỒI CẢ CHUỖI khi thấy dùng lại.
   Gọi refresh song song 5 lần là tự đá mình ra khỏi phiên. */
let refreshing: Promise<void> | null = null;
let onLogout: (() => void) | null = null;
export const setOnLogout = (fn: () => void) => { onLogout = fn; };

const runRefresh = () => {
  refreshing ??= apiClient
    .post("/auth/refresh")
    .then(() => undefined)
    .finally(() => { refreshing = null; });
  return refreshing;
};

apiClient.interceptors.response.use(
  (r) => r,
  async (error: AxiosError) => {
    const cfg = error.config as AxiosRequestConfig & { _retried?: boolean };
    const isAuthPath = typeof cfg?.url === "string" && cfg.url.startsWith("/auth/");

    if (error.response?.status === 401 && cfg && !cfg._retried && !isAuthPath) {
      cfg._retried = true;
      try {
        await runRefresh();
        return apiClient(cfg);
      } catch {
        onLogout?.();
      }
    }
    return Promise.reject(error);
  },
);
