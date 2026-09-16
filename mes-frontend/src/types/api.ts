/** Hình dạng lỗi thống nhất của backend — `main.py` luôn trả đúng hai khoá này. */
export type ApiError = { code: string; message: string; status: number };

export type OkOut = { ok: boolean; message: string };
export type SessionOut = { full_name: string; roles: string[] };
export type StationTokenOut = { station: number; token: string };
