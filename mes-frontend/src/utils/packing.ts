import type { TraceRound } from "@/types/trace";

/**
 * Đối chiếu sổ đóng thùng với sản lượng chuyền.
 *
 * Backend trả `box_summary.le_pcs = made − packed` và màn hình cũ gọi nó là
 * "Thùng lẻ — chưa đủ thùng". Sai: với quy cách 200, chênh 800 là BỐN THÙNG ĐẦY
 * chưa ai ghi sổ, lẻ thật bằng 0. Hai thứ đó khác hẳn nhau — một cái là việc còn
 * phải làm, một cái là bình thường không phải làm gì.
 *
 * Gộp chung khiến con số duy nhất có thể chặn được việc chốt hụt lại mang nhãn
 * "KHÔNG phải hàng thiếu". Tách ở đây, không đọc `le_pcs` nữa.
 */
export type BoxReconcile = {
  boxesLogged: number;
  packedPcs: number;
  madePcs: number;
  /** made − packed, không âm. */
  diffPcs: number;
  /** Thùng ĐẦY đã đóng nhưng sổ giờ chưa ghi — sổ đang chạy sau thực tế. */
  unloggedBoxes: number;
  /**
   * Phần chưa đủ một thùng đầy. KHÔNG phải việc còn phải làm: nó vào THÙNG LẺ
   * CUỐI lúc kết thúc đóng thùng (§7b.2). Sổ giờ chỉ đếm thùng đầy nên phần này
   * không bao giờ xuất hiện ở đó — chênh bằng đúng nó là chuyện bình thường.
   */
  loosePcs: number;
  matched: boolean;
};

/**
 * Phân rã pcs thành thùng đầy + thùng lẻ cuối — BRD §7b.2.
 *
 * "Thùng cuối của đơn được đóng THIẾU: đó là mặc định, không phải ngoại lệ."
 * Đơn nào không chia hết cho quy cách cũng có một thùng cuối không đầy. Bắt thùng
 * nào cũng phải đầy thì đơn không bao giờ đóng được — vĩnh viễn thiếu vài trăm
 * cái cho đủ thùng, mà làm thêm cho đủ là sản xuất dư khách không đặt.
 */
export function boxBreakdown(pcs: number, pcsPerBox: number) {
  if (pcsPerBox <= 0) return { full: 0, last: pcs };
  return { full: Math.floor(pcs / pcsPerBox), last: pcs % pcsPerBox };
}

export function reconcileBoxes(
  round: TraceRound | null,
  pcsPerBox: number,
): BoxReconcile {
  const b = round?.box_summary;
  const packedPcs = b?.packed_pcs ?? 0;
  const madePcs = b?.made_pcs ?? 0;
  const diffPcs = Math.max(0, madePcs - packedPcs);

  return {
    boxesLogged: b?.boxes_total ?? 0,
    packedPcs,
    madePcs,
    diffPcs,
    unloggedBoxes: pcsPerBox > 0 ? Math.floor(diffPcs / pcsPerBox) : 0,
    loosePcs: pcsPerBox > 0 ? diffPcs % pcsPerBox : diffPcs,
    matched: diffPcs === 0,
  };
}
