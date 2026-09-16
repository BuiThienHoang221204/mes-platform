/** Sáu trạm — một nguồn duy nhất, chép từ `app/common/vocab/enums.py`. */
export const STATIONS = [
  { no: 0, name: "Kho xuất", route: "/warehouse-out" },
  { no: 1, name: "Setup máy", route: "/setup" },
  { no: 2, name: "QC", route: "/qc" },
  { no: 3, name: "Bàn team leader", route: "/waiting" },
  { no: 4, name: "Sản xuất", route: "/production" },
  { no: 5, name: "Kho nhập", route: "/warehouse-in" },
] as const;

export type Station = (typeof STATIONS)[number];

export const stationName = (no: number) =>
  STATIONS.find((s) => s.no === no)?.name ?? `Trạm ${no}`;

export const stationRoute = (no: number) =>
  STATIONS.find((s) => s.no === no)?.route ?? "/scan";
