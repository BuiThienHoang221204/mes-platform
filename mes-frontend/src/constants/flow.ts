import { STATIONS } from "./stations";

export type StationFlowInfo = {
  from: string;
  here: string;
  next: string;
  back?: string;
};

export const STATION_FLOW: Record<number, StationFlowInfo> = {
  0: {
    from: "Kế hoạch chốt MO",
    here: "Quét nhận MO rồi bàn giao xuống xưởng",
    next: "Setup máy",
  },
  1: {
    from: "Lấy nguyên liệu bàn giao",
    here: "Canh máy, gá khuôn — làm xong KHÔNG bấm gì",
    next: "Team Leader quét nhận là bước này tự đóng",
  },
  2: {
    from: "Setup máy",
    here: "Giữ lệnh, chờ chia chuyền",
    next: "Sản xuất",
  },
  3: {
    from: "Team Leader",
    here: "Chia chuyền, chạy, ghi sản lượng từng giờ, đóng thùng",
    next: "Kho nhập",
  },
  4: {
    from: "Sản xuất đóng thùng xong",
    here: "Đối chiếu số lượng rồi nhập kho",
    next: "Đủ → Hoàn thành lệnh",
    back: "Thiếu → về Team Leader, mở vòng mới",
  },
};

export const WAITING_SINCE: Record<number, string> = {
  0: "Chờ từ lúc mở vòng",
  1: "Chờ từ lúc Lấy nguyên liệu bàn giao",
  2: "Chờ từ lúc Setup máy quét nhận",
  3: "Chờ từ lúc Team Leader quét nhận",
  4: "Chờ từ lúc đóng thùng xong",
};

export const waitingSince = (station: number) => WAITING_SINCE[station] ?? "Thời gian chờ";

export const flowOf = (station: number) => STATION_FLOW[station];

export const prevStation = (n: number) => (n > 0 ? STATIONS[n - 1] : null);
export const nextStation = (n: number) => (n < STATIONS.length - 1 ? STATIONS[n + 1] : null);
