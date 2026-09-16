/**
 * MỌI giá trị trạng thái đi qua đây — chép từ `mes-backend/app/common/vocab/enums.py`
 * và `app/modules/warehouse_in/schemas.py`.
 *
 * Cùng lý lẽ với `errorCodes.ts`: gõ `"DRAFT"` rải rác thì sai một chữ là so sánh
 * luôn trả `false` mà **không ai báo gì** — chuỗi nào cũng hợp lệ với TypeScript
 * khi nó nằm trong một `string`. Qua hằng thì gõ sai là lỗi biên dịch ngay.
 *
 * Nhãn tiếng Việt cũng để ở đây: một trạng thái chỉ được hiện bằng ĐÚNG MỘT chữ
 * trên toàn app. Trước đây mỗi màn tự đặt tên là người vận hành đọc ra ba nghĩa.
 */

/* ── Trạng thái lệnh — khớp ENUM `mo_status` dưới CSDL ───────────────────── */
export const MO_STATUS = {
  DRAFT: "DRAFT",
  SUBMITTED: "SUBMITTED",
  PROCESSING: "PROCESSING",
  COMPLETED: "COMPLETED",
  CANCELLED: "CANCELLED",
} as const;
export type MoStatusValue = (typeof MO_STATUS)[keyof typeof MO_STATUS];

export const MO_STATUS_LABEL: Record<MoStatusValue, string> = {
  [MO_STATUS.DRAFT]: "Nháp",
  [MO_STATUS.SUBMITTED]: "Đã chốt",
  [MO_STATUS.PROCESSING]: "Đang chạy",
  [MO_STATUS.COMPLETED]: "Hoàn thành",
  [MO_STATUS.CANCELLED]: "Đã huỷ",
};

export type PillTone = "accent" | "ok" | "warn" | "danger" | "flat";

export const MO_STATUS_TONE: Record<MoStatusValue, PillTone> = {
  [MO_STATUS.DRAFT]: "flat",
  [MO_STATUS.SUBMITTED]: "accent",
  [MO_STATUS.PROCESSING]: "accent",
  [MO_STATUS.COMPLETED]: "ok",
  [MO_STATUS.CANCELLED]: "danger",
};

/** Bộ lọc ở màn Kế hoạch — thứ tự đúng theo vòng đời một lệnh. */
export const MO_FILTERS = [
  MO_STATUS.DRAFT,
  MO_STATUS.PROCESSING,
  MO_STATUS.COMPLETED,
  MO_STATUS.CANCELLED,
] as const;

/* ── Kết quả QC — khớp ENUM `qc_verdict` ─────────────────────────────────── */
export const QC_RESULT = { PASS: "PASS", FAIL: "FAIL" } as const;
export type QcResultValue = (typeof QC_RESULT)[keyof typeof QC_RESULT];

export const QC_RESULT_LABEL: Record<QcResultValue, string> = {
  [QC_RESULT.PASS]: "Đạt",
  [QC_RESULT.FAIL]: "Không đạt",
};

/* ── Kết quả nhập kho — `WarehouseInCompleteOut.outcome` ─────────────────── */
export const WI_OUTCOME = {
  /** Đủ số lượng — đơn đóng lại. */
  COMPLETED: "COMPLETED",
  /** Chưa đủ — tự mở vòng mới về Bàn team leader (§6b). */
  ROUND_OPENED: "ROUND_OPENED",
} as const;
export type WiOutcomeValue = (typeof WI_OUTCOME)[keyof typeof WI_OUTCOME];

/* ── Loại đoạn chuyền — khớp ENUM `segment_kind` ─────────────────────────── */
export const SEGMENT_KIND = { WAIT: "WAIT", RUN: "RUN" } as const;
export const SEGMENT_KIND_LABEL = {
  [SEGMENT_KIND.WAIT]: "Chờ xử lý",
  [SEGMENT_KIND.RUN]: "Đang lắp ráp",
} as const;
