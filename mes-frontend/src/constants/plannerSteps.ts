import type { StationStep } from "./stationSteps";

export const PLANNER_ROUTE = "/mos";

export const PLANNER_STEPS: StationStep[] = [
  { id: "dash", name: "Tổng quan", sub: "Toàn xưởng một màn hình" },
  { id: "create", name: "Tạo lệnh", sub: "Lẻ · nhập CSV" },
  { id: "book", name: "Sổ lệnh", sub: "Chốt · huỷ" },
  { id: "board", name: "Bảng đang chạy", sub: "Mọi trạm" },
];

export const TRACE_ROUTE = "/trace";

export const PLANNER_TRACE_STEP = "trace";

export const resolvePlannerStep = (id: string | null) =>
  PLANNER_STEPS.find((s) => s.id === id)?.id ?? PLANNER_STEPS[0].id;
