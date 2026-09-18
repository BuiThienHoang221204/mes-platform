import type { MoStatus } from "@/types/mo";

export type MoProgressRow = {
  code: string;
  product_name: string;
  status: MoStatus;
  quantity: number;
  /** pcs ĐÃ ĐÓNG THÙNG nhập kho, không phải SL đạt (§6b.2). */
  qty_done: number;
  qty_remain: number;
  qty_ok_total: number;
  qty_ng_total: number;
  qty_short_total: number;
  rounds_done: number;
};

export type HourlyPoint = {
  at: string;
  at_end: string;
  qty: number;
  target_qty: number;
  headcount: number | null;
  slots: number;
};

export type HourlySeries = {
  code: string;
  points: HourlyPoint[];
};

/** Sáu mốc giờ ca, do server giữ — không chép lại thành hằng số ở đây. */
export type ShiftMarks = {
  day_start: number;
  shift_start: number;
  lunch_start: number;
  lunch_end: number;
  shift_end: number;
  day_end: number;
};

export type HourlyReport = {
  bucket: number;
  target_pct: number;
  shift: ShiftMarks;
  series: HourlySeries[];
  /** Dòng chưa khai định mức — loại khỏi cả tử lẫn mẫu. */
  skipped_rows: number;
  /** Dòng ghi ngoài giờ đi làm, đã ghép vào khung gần nhất. */
  folded_rows: number;
};

export type HourlyQuery = {
  bucket: number;
  dateFrom: string;
  dateTo: string;
};
