import { postData } from "./http";
import type { OkOut } from "@/types/api";
import type { QcOut, ScanOut, WarehouseInOut } from "@/types/mo";
import type { QcResultValue } from "@/constants/status";

/**
 * `POST /scan` là thao tác NHẬN của CẢ SÁU TRẠM (FE-PLAN §8.1).
 * Trạm suy từ VAI người quét. Chỉ vai đa trạm (Bàn team leader, PLANNER) mới
 * phải khai `station`; server luôn kiểm lại quyền.
 */
export const stationService = {
  scan: (raw: string, station?: number | null) =>
    postData<ScanOut>("/scan", station == null ? { raw } : { raw, station }),

  handover: (code: string) => postData<OkOut>(`/warehouse-out/${code}/handover`),

  handoverBatch: (codes: string[]) =>
    postData<OkOut>("/warehouse-out/handover-batch", codes),

  qc: (code: string, result: QcResultValue, reason?: { codeId?: number | null; text?: string | null }) =>
    postData<QcOut>(`/qc/${code}`, {
      result,
      reason_code_id: reason?.codeId ?? null,
      reason_text: reason?.text ?? null,
    }),

  // Không gửi số nào lên: số nhập kho LÀ số đã đóng thùng (§8), server tự lấy.
  warehouseIn: (code: string) =>
    postData<WarehouseInOut>(`/warehouse-in/${code}/complete`),
};
