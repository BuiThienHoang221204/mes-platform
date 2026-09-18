import type { StationStep } from "./stationSteps";

export const REPORT_ROUTE = "/reports";

/** Ba màn của Báo cáo sản xuất — ba câu hỏi khác nhau, nên ba trang khác nhau. */
export const REPORT_STEPS: StationStep[] = [
  { id: "progress", name: "Tiến độ MO", sub: "Đơn nào sắp xong" },
  { id: "hourly", name: "Năng suất theo giờ", sub: "Giờ nào chuyền không đạt định mức" },
  { id: "steps", name: "MO theo giai đoạn", sub: "Hàng đang dồn ở khúc nào" },
];

export const resolveReportStep = (id: string | null) =>
  REPORT_STEPS.find((s) => s.id === id)?.id ?? REPORT_STEPS[0].id;
