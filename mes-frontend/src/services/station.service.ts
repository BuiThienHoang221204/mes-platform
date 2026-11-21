import { postData } from "./http";
import type { OkOut } from "@/types/api";
import type { ScanOut, WarehouseInOut } from "@/types/mo";

/**
 * `POST /scan` là thao tác NHẬN của CẢ NĂM TRẠM (FE-PLAN §8.1).
 * Trạm suy từ VAI người quét. Chỉ vai đa trạm (Bàn team leader, PLANNER) mới
 * phải khai `station`; server luôn kiểm lại quyền.
 */
export const stationService = {
  scan: (raw: string, station?: number | null) =>
    postData<ScanOut>("/scan", station == null ? { raw } : { raw, station }),

  handover: (code: string) => postData<OkOut>(`/warehouse-out/${code}/handover`),

  handoverBatch: (codes: string[]) =>
    postData<OkOut>("/warehouse-out/handover-batch", codes),

  // Không gửi số nào lên: số nhập kho LÀ số đã đóng thùng (§8), server tự lấy.
  warehouseIn: (code: string) =>
    postData<WarehouseInOut>(`/warehouse-in/${code}/complete`),
};
