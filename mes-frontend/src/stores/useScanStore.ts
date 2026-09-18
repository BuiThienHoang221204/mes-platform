import { create } from "zustand";
import type { ScanOut } from "@/types/mo";

/**
 * Kết quả lần quét vừa rồi — và TRẠM nào đã quét.
 *
 * Store là toàn cục nên trước đây câu phản hồi đi theo người dùng sang trạm khác:
 * quét ở Kho xuất rồi bấm sang Setup thì vẫn thấy dải xanh "Kho xuất đã nhận".
 * Đứng ở màn Setup mà đọc câu đó thì hiểu là Setup vừa nhận xong — sai hẳn việc.
 *
 * Nên `station` đi kèm kết quả, và `ScanFeedback` chỉ hiện khi đúng trạm đang mở.
 * Ghi kèm trạm đáng tin hơn là nhớ gọi `reset()` ở mọi chỗ điều hướng: quên một
 * chỗ là lỗi quay lại, mà lần này nó im lặng.
 */
type ScanState = {
  last: ScanOut | null;
  lastError: string | null;
  /** Trạm phát ra kết quả đang giữ. `null` khi chưa quét gì. */
  station: number | null;
  draft: string;
  setResult: (station: number, r: ScanOut) => void;
  setError: (station: number, m: string) => void;
  setDraft: (code: string) => void;
  reset: () => void;
};

export const useScanStore = create<ScanState>((set) => ({
  last: null,
  lastError: null,
  station: null,
  draft: "",
  setResult: (station, last) => set({ station, last, lastError: null, draft: "" }),
  setError: (station, lastError) => set({ station, lastError, last: null }),
  setDraft: (draft) => set({ draft }),
  reset: () => set({ last: null, lastError: null, station: null, draft: "" }),
}));
