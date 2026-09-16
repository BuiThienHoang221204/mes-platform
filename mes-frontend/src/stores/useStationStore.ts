import { create } from "zustand";
import { persist } from "zustand/middleware";

/**
 * Cấu hình của CÁI MÁY TÍNH BẢNG, không phải của người dùng.
 *
 * Đây là ngoại lệ DUY NHẤT của luật "không lưu token ở localStorage" — token
 * này gắn với thiết bị đặt cố định ở trạm, và không cấp quyền gì ngoài việc
 * khai báo mình đứng ở trạm nào (FE-PLAN §7.3 R22).
 */
type StationState = {
  station: number | null;
  stationToken: string | null;
  setStation: (station: number, token: string) => void;
  clear: () => void;
};

export const useStationStore = create<StationState>()(
  persist(
    (set) => ({
      station: null,
      stationToken: null,
      setStation: (station, stationToken) => set({ station, stationToken }),
      clear: () => set({ station: null, stationToken: null }),
    }),
    { name: "mes-station" },
  ),
);
