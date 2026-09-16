import { STATIONS } from "./stations";

/**
 * Câu trả lời cho ba câu hỏi mà người đứng ở trạm luôn hỏi: lệnh này từ đâu tới,
 * ở đây tôi phải làm gì, xong thì nó đi đâu.
 *
 * Chép từ luồng trong `demo/mes-v2-console.html` và BRD §3–§8. Hai trạm có ngã rẽ
 * (QC không đạt, Kho nhập thiếu hàng) — ngã rẽ phải nói ra, vì đó đúng là lúc
 * người vận hành hoang mang nhất.
 */
export type StationFlowInfo = {
  from: string;
  here: string;
  next: string;
  /** Nhánh quay lui — có thì hiện thành dòng cảnh báo riêng. */
  back?: string;
};

export const STATION_FLOW: Record<number, StationFlowInfo> = {
  0: {
    from: "Kế hoạch chốt lệnh",
    here: "Quét nhận lệnh rồi bàn giao xuống xưởng",
    next: "Setup máy",
  },
  1: {
    from: "Kho xuất bàn giao",
    here: "Canh máy, gá khuôn — làm xong KHÔNG bấm gì",
    next: "QC quét nhận là bước này tự đóng",
  },
  2: {
    from: "Setup máy",
    here: "Kiểm hàng đầu, ra kết quả Đạt hoặc Không đạt",
    next: "Đạt → Bàn team leader",
    back: "Không đạt → về Kho xuất, mở vòng mới",
  },
  3: {
    from: "QC đạt",
    here: "Giữ lệnh, chờ chia chuyền",
    next: "Sản xuất",
  },
  4: {
    from: "Bàn team leader",
    here: "Chia chuyền, chạy, ghi sản lượng từng giờ, đóng thùng",
    next: "Kho nhập",
  },
  5: {
    from: "Sản xuất đóng thùng xong",
    here: "Đối chiếu số lượng rồi nhập kho",
    next: "Đủ → Hoàn thành lệnh",
    back: "Thiếu → về Bàn team leader, mở vòng mới",
  },
};

/**
 * Hàng đợi mỗi trạm đếm giờ chờ từ một MỐC KHÁC NHAU — "bắt đầu chờ" ở mỗi trạm
 * là một sự kiện khác. Khớp từng chữ với `waiting_sec` trong `board/repository.py`;
 * lệch một chỗ là màn hình giải thích sai con số của chính nó.
 */
export const WAITING_SINCE: Record<number, string> = {
  0: "Chờ từ lúc mở vòng",
  1: "Chờ từ lúc Kho xuất bàn giao",
  2: "Chờ từ lúc Setup máy quét nhận",
  3: "Chờ từ lúc QC ra kết quả Đạt",
  4: "Chờ từ lúc Bàn team leader quét nhận",
  5: "Chờ từ lúc đóng thùng xong",
};

export const waitingSince = (station: number) => WAITING_SINCE[station] ?? "Thời gian chờ";

export const flowOf = (station: number) => STATION_FLOW[station];

/** Trạm trước và trạm sau theo thứ tự 0→5. `null` ở hai đầu chuỗi. */
export const prevStation = (n: number) => (n > 0 ? STATIONS[n - 1] : null);
export const nextStation = (n: number) => (n < STATIONS.length - 1 ? STATIONS[n + 1] : null);
