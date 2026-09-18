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
      { id: "decide", name: "Đạt / Không đạt", sub: "Không đạt bắt buộc ghi lý do" },
    ],
  },
  3: {
    steps: [
      { id: "scan", name: "Quét nhận", sub: "Hàng đợi + nhận tại trạm" },
      { id: "dispatch", name: "Chờ vào chuyền", sub: "Và toàn quyền Step 4" },
    ],
  },
  // Trước đây trạm 4 có BẢY bước, bốn trong số đó là một nhánh rẽ đôi vẽ trên
  // thanh bước. Nhánh song song §7b là ràng buộc THỨ TỰ ở backend, không phải
  // cấu trúc điều hướng — vẽ nó ra thanh bước là bắt người vận hành dịch một đồ
  // thị phụ thuộc thành thao tác bấm. Và "Sản lượng giờ" vốn không phải một bước:
  // nó lặp 8-10 lần một ca, xếp ngang hàng với "Chốt sổ SX" là sai loại.
  4: {
    steps: [
      { id: "scan", name: "Quét nhận", sub: "Hàng đợi + nhận tại trạm" },
      { id: "work", name: "Chạy & đóng thùng", sub: "Chuyền · sản lượng giờ · chốt sổ" },
      { id: "board", name: "Bảng đang chạy", sub: "Mọi lệnh một màn hình" },
    ],
  },
  5: {
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
