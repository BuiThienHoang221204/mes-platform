/**
 * `/board/queue/{station}`, `/board/running`, `/mos/{code}/trace` CHƯA gắn
 * `response_model` ở backend (cố ý — trả thêm field tuỳ trạm). Kiểu ở đây khai
 * theo response THẬT và phải kiểm lại khi backend đổi (FE-PLAN §8.3).
 */
export type QueueRow = {
  /** Backend trả `code`, KHÔNG phải `mo_code` — khai sai thì cột mã hiện trống
      mà không có lỗi nào nổ ra. */
  code: string;
  product_name: string;
  quantity: number;
  round_no: number;
  target_qty?: number;
  waiting_sec?: number;
  /** Riêng hàng đợi trạm 5 — hai số này đi cùng nhau để quy pcs ra THÙNG. */
  qty_packed?: number;
  pcs_per_box?: number;
};

/** `/board/at/{station}` — lệnh ĐANG trong tay trạm, khác hẳn hàng đợi. */
export type AtStationRow = {
  code: string;
  product_name: string;
  quantity: number;
  pcs_per_box: number;
  round_no: number;
  target_qty: number;
  accepted_at: string;
  accepted_by: string;
  holding_sec: number;
  /** Trạm 0 — đã bàn giao xuống xưởng chưa. */
  handed_over_at: string | null;
  /** Trạm 5 — đã đóng được bao nhiêu, xong lúc nào. */
  qty_packed: number | null;
  packing_done_at: string | null;
  /**
   * Trạm 2 — đã kết luận chưa. QC vẫn giữ lệnh SAU KHI ra kết quả, vì bước chỉ
   * đóng khi Bàn team leader quét nhận. Nên "còn trong tay QC" không có nghĩa là
   * "chưa có kết quả", và chỉ trường này phân biệt được.
   */
  qc_result: "PASS" | "FAIL" | null;
  qc_checked_at: string | null;
};

export type BoardLine = {
  line_code: string;
  current_kind: "WAIT" | "RUN" | null;
  hold_reason: string | null;
  wait_sec: number;
  run_sec: number;
};

export type RunningRow = {
  code: string;
  product_name: string;
  quantity: number;
  round_no: number;
  target_qty: number;
  required_sec: number;
  actual_sec: number | null;
  on_time: boolean | null;
  late_sec: number | null;
  qty_ok: number | null;
  qty_ng: number | null;
  qty_short: number | null;
  production_closed_at: string | null;
  qty_packed: number | null;
  packing_done_at: string | null;
  handed_over_at: string | null;
  /**
   * Bước cao nhất đã quét nhận trong vòng. `null` = chưa bước nào nhận, lệnh vừa
   * chốt và còn nằm ở hàng chờ Kho xuất. Bảng đang chạy hiện lệnh ở MỌI bước
   * (BRD §9b.5) nên đây là cột duy nhất nói được hàng đang ở đâu — thiếu nó thì
   * lệnh chưa ra khỏi kho trông giống hệt lệnh đang lắp ráp dở.
   */
  current_step: number | null;
  lines: BoardLine[];
};

/**
 * Hai con số mỗi trạm, không phải một. `counts` là việc CHƯA AI NHẬN — có người
 * phải đi quét. `holding` là việc ĐANG trong tay trạm — đang chạy, không ai cần
 * làm gì thêm. Gộp lại thì xưởng chạy ba lệnh ở Sản xuất mà màn hình hiện 0.
 */
export type StationCounts = {
  counts: Record<string, number>;
  holding: Record<string, number>;
};
