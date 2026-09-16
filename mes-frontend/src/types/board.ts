/**
 * `/board/queue/{station}`, `/board/running`, `/mos/{code}/trace` CHƯA gắn
 * `response_model` ở backend (cố ý — trả thêm field tuỳ trạm). Kiểu ở đây khai
 * theo response THẬT và phải kiểm lại khi backend đổi (FE-PLAN §8.3).
 */
export type QueueRow = {
  /** Backend trả `code`, KHÔNG phải `mo_code` — khai sai thì cột mã hiện trống
      mà không có lỗi nào nổ ra. */
  code: string;
  product_name: string;
  quantity: number;
  round_no: number;
  target_qty?: number;
  waiting_sec?: number;
  qty_packed?: number;       // riêng hàng đợi trạm 5
};

/** `/board/at/{station}` — lệnh ĐANG trong tay trạm, khác hẳn hàng đợi. */
export type AtStationRow = {
  code: string;
  product_name: string;
  quantity: number;
  pcs_per_box: number;
  round_no: number;
  target_qty: number;
  accepted_at: string;
  accepted_by: string;
  holding_sec: number;
  /** Trạm 0 — đã bàn giao xuống xưởng chưa. */
  handed_over_at: string | null;
  /** Trạm 5 — đã đóng được bao nhiêu, xong lúc nào. */
  qty_packed: number | null;
  packing_done_at: string | null;
};

export type RunningRow = {
  code: string;
  product_name: string;
  round_no: number;
  target_qty: number;
  lines?: string[];
  qty_ok?: number | null;
  qty_packed?: number | null;
  actual_sec?: number | null;
  required_sec?: number | null;
  on_time?: boolean | null;
};

export type StationCounts = { counts: Record<string, number> };
