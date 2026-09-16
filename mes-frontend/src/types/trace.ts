/**
 * `/mos/{code}/trace` — nguồn DUY NHẤT của màn Sản xuất.
 * Backend cố ý không gắn `response_model`, nên kiểu ở đây phải kiểm lại tay
 * mỗi khi backend đổi (FE-PLAN §8.3).
 */
export type TraceLine = { line_code: string; wait_sec: number; run_sec: number };

export type TraceHourly = {
  work_date: string;
  slot_hour: number;
  headcount: number | null;
  target_qty: number | null;
  qty: number;
  note: string | null;
};

export type TraceBoxHourly = {
  work_date: string;
  slot_hour: number;
  boxes: number;
  pcs_per_box: number;
  note: string | null;
};

/** `le_pcs` do server tính — FE KHÔNG tự tính lại (R23). */
export type BoxSummary = {
  boxes_total: number;
  packed_pcs: number;
  made_pcs: number;
  le_pcs: number;
};

export type TraceRound = {
  round_no: number;
  started_from: number | null;
  target_qty: number;
  required_sec: number;
  closed_at: string | null;
  lines: TraceLine[];
  hourly: TraceHourly[];
  packing_hourly: TraceBoxHourly[];
  box_summary: BoxSummary;
  production: { qty_ok: number; qty_ng: number; qty_short: number } | null;
  packing: { qty_packed: number | null; started_at: string; completed_at: string | null } | null;
};

export type Trace = {
  code: string;
  product_name: string;
  quantity: number;
  pcs_per_box: number;
  status: string;
  rounds: TraceRound[];
};
