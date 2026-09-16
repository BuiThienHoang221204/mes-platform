import { postData } from "./http";
import type { OkOut } from "@/types/api";
import type { QcOut, ScanOut, WarehouseInOut } from "@/types/mo";
import type { QcResultValue } from "@/constants/status";

/**
 * `POST /scan` là thao tác NHẬN của CẢ SÁU TRẠM (FE-PLAN §8.1).
 * Trạm lấy từ header `X-Station-Token` — KHÔNG lấy từ body, vì mã QR chỉ nói
 * MO nào chứ không nói bước nào (BRD §1b.3).
 */
export const stationService = {
  scan: (raw: string, stationToken: string) =>
    postData<ScanOut>("/scan", { raw }, { headers: { "X-Station-Token": stationToken } }),

  handover: (code: string) => postData<OkOut>(`/warehouse-out/${code}/handover`),

  qc: (code: string, result: QcResultValue, reason_text?: string) =>
    postData<QcOut>(`/qc/${code}`, { result, reason_code_id: null, reason_text: reason_text ?? null }),

  warehouseIn: (code: string, qty_received?: number | null) =>
    postData<WarehouseInOut>(`/warehouse-in/${code}/complete`, { qty_received: qty_received ?? null }),
};
