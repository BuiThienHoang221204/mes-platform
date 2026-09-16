import type { MoStatusValue, QcResultValue, WiOutcomeValue } from "@/constants/status";

/** Kiểu SUY RA từ hằng ở `constants/status.ts` — khai lại là hai chỗ phải sửa. */
export type MoStatus = MoStatusValue;

export type MoOut = {
  code: string;
  product_name: string;
  quantity: number;
  pcs_per_box: number;
  unit: string;
  status: MoStatus;
  required_production_sec: number;
};

export type ScanOut = {
  ok: boolean;
  mo_code: string;
  station: number;
  round_no: number;
  message: string;
  duplicate: boolean;
};

export type QcOut = { result: QcResultValue; new_round_no: number | null; message: string };

export type WarehouseInOut = {
  outcome: WiOutcomeValue;
  qty_done: number;
  qty_remain: number;
  new_round_no: number | null;
  message: string;
};

export type PackingHourlyOut = {
  boxes: number;
  pcs_per_box: number;
  packed_pcs: number;
  made_pcs: number;
  le_pcs: number;
  message: string;
};
