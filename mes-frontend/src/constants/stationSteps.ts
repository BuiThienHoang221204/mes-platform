export type StationStep = {
  id: string;
  name: string;
  sub: string;
};

export type StationFlow = {
  steps: StationStep[];
};

export const STATION_STEPS: Record<number, StationFlow> = {
  0: {
    steps: [
      { id: "scan", name: "Quét nhận", sub: "Hàng đợi + nhận tại trạm" },
      { id: "handover", name: "Bàn giao", sub: "Giao xuống Setup" },
      { id: "slip", name: "Xem phiếu", sub: "Tra cứu — không ghi sổ" },
    ],
  },
  1: {
    steps: [
      { id: "scan", name: "Quét nhận", sub: "Hàng đợi + nhận tại trạm" },
      { id: "working", name: "Đang setup", sub: "Không có nút Complete" },
    ],
  },
  2: {
    steps: [
      { id: "scan", name: "Quét nhận", sub: "Hàng đợi + nhận tại trạm" },
      { id: "dispatch", name: "Chờ vào chuyền", sub: "Và toàn quyền Step 3" },
    ],
  },
  3: {
    steps: [
      { id: "scan", name: "Quét nhận", sub: "Hàng đợi + nhận tại trạm" },
      { id: "work", name: "Chạy & đóng thùng", sub: "Chuyền · sản lượng giờ · chốt sổ" },
      { id: "board", name: "Bảng đang chạy", sub: "Mọi lệnh một màn hình" },
    ],
  },
  4: {
    steps: [
      { id: "scan", name: "Quét nhận", sub: "Hàng đợi + nhận tại trạm" },
      { id: "finish", name: "Hoàn thành", sub: "Đủ số hay trả về vòng mới" },
    ],
  },
};

export const stepsOf = (station: number) => STATION_STEPS[station]?.steps ?? [];

export const firstStepId = (station: number) => stepsOf(station)[0]?.id ?? "scan";

export const resolveStep = (station: number, id: string | null) =>
  stepsOf(station).find((s) => s.id === id)?.id ?? firstStepId(station);
