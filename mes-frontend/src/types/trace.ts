export type TraceLine = {
  line_code: string;
  wait_sec: number;
  run_sec: number;
  current_kind: "WAIT" | "RUN" | null;
  hold_reason_text: string | null;
  current_since: string | null;
};

export type TraceStep = {
  step_no: number;
  name: string;
  accepted_at: string;
  accepted_by: string | null;
  closed_at: string | null;
  closed_by: string | null;
};

export type TraceHourly = {
  work_date: string;
  slot_hour: number;
  headcount: number | null;
  target_qty: number | null;
  qty: number;
  note: string | null;
  recorded_at: string;
};

export type TraceBoxHourly = {
  work_date: string;
  slot_hour: number;
  boxes: number;
  pcs_per_box: number;
  note: string | null;
  recorded_at: string;
};

export type BoxSummary = {
  boxes_total: number;
  packed_pcs: number;
  made_pcs: number;
  le_pcs: number;
};

export type TraceProduction = {
  qty_ok: number;
  qty_ng: number;
  qty_short: number;
  ng_reason_text: string | null;
  short_reason_text: string | null;
  closed_at: string | null;
};

export type TracePacking = {
  qty_packed: number | null;
  note_text: string | null;
  started_at: string;
  completed_at: string | null;
};

export type TraceRound = {
  round_no: number;
  started_from: number | null;
  opened_at: string;
  closed_at: string | null;
  target_qty: number;
  required_sec: number;
  return_reason_text: string | null;
  steps: TraceStep[];
  lines: TraceLine[];
  /** TRANG ĐẦU của sổ giờ. Tổng thật ở `hourly_total` — đừng cộng mảng này. */
  hourly: TraceHourly[];
  hourly_total: number;
  /** Cộng trên MỌI dòng, do server tính. Màn Sản xuất lấy nó làm "số đã làm ra". */
  hourly_qty_total: number;
  hourly_target_total: number;

  /** TRANG ĐẦU của sổ thùng. */
  packing_hourly: TraceBoxHourly[];
  packing_hourly_total: number;
  box_summary: BoxSummary;
  production: TraceProduction | null;
  packing: TracePacking | null;
};

export type MoProgress = {
  mo_id: string;
  code: string;
  quantity: number;
  qty_done: number;
  qty_ok_total: number;
  qty_ng_total: number;
  qty_short_total: number;
  qty_remain: number;
  rounds_done: number;
};

export type StepTotal = { step_no: number; sec: number; rounds: number };

export type TraceEvent = {
  at: string;
  action: string;
  step_no: number | null;
  from: string | null;
  to: string | null;
  reason: string | null;
};

export type Trace = {
  code: string;
  product_name: string;
  quantity: number;
  pcs_per_box: number;
  status: string;
  progress: MoProgress;
  step_totals: StepTotal[];
  rounds: TraceRound[];
  /** CHỈ trang đầu. Phần còn lại lấy qua `/mos/{code}/events`. */
  events: TraceEvent[];
  events_total: number;
};

export type EventPage = { items: TraceEvent[]; total: number };
