export const REASON_GROUP = {
  HOLD: "HOLD",
  NG: "NG",
  SHORT: "SHORT",
  QC: "QC",
  PACKING: "PACKING",
} as const;

export type ReasonGroupValue = (typeof REASON_GROUP)[keyof typeof REASON_GROUP];

export const REASON_GROUP_LABEL: Record<ReasonGroupValue, string> = {
  [REASON_GROUP.HOLD]: "Lý do dừng chuyền",
  [REASON_GROUP.NG]: "Lý do hỏng",
  [REASON_GROUP.SHORT]: "Lý do thiếu",
  [REASON_GROUP.QC]: "Lý do không đạt",
  [REASON_GROUP.PACKING]: "Ghi chú đóng thùng",
};
