/** Hình dạng lỗi thống nhất của backend — `main.py` luôn trả đúng hai khoá này. */
export type ApiError = { code: string; message: string; status: number };

/**
 * Một TRANG của một danh sách — khuôn duy nhất của mọi API trả danh sách.
 *
 * `total` là tổng SAU KHI lọc, không phải số dòng trong trang. Thiếu nó thì nút
 * `Xem thêm` hoặc tắt vĩnh viễn hoặc bấm mãi không hết.
 */
export type Page<T> = { items: T[]; total: number };

export type OkOut = { ok: boolean; message: string };
export type SessionOut = { full_name: string; roles: string[] };
export type StationTokenOut = { station: number; token: string };
