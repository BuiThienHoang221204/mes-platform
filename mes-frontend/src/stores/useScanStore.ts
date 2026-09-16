import { create } from "zustand";
import type { ScanOut } from "@/types/mo";

/** Trạng thái UI thuần của màn quét — không có gì lấy từ API bị giữ lâu ở đây. */
type ScanState = {
  last: ScanOut | null;
  lastError: string | null;
  setResult: (r: ScanOut) => void;
  setError: (m: string) => void;
  reset: () => void;
};

export const useScanStore = create<ScanState>((set) => ({
  last: null,
  lastError: null,
  setResult: (last) => set({ last, lastError: null }),
  setError: (lastError) => set({ lastError, last: null }),
  reset: () => set({ last: null, lastError: null }),
}));
