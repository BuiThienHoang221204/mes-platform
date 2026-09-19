import { PAGE_SIZE } from "@/constants/pagination";

/**
 * R2 — Query key CHỈ lấy từ đây. Gõ tay ở hai chỗ thì `invalidateQueries`
 * trượt, và nó trượt IM LẶNG, không báo lỗi gì.
 */
export const boardKeys = {
  all: ["board"] as const,
  running: (offset = 0, limit = PAGE_SIZE) =>
    [...boardKeys.all, "running", limit, offset] as const,
  queue: (station: number) => [...boardKeys.all, "queue", station] as const,
  atStation: (station: number) => [...boardKeys.all, "at", station] as const,
  overview: () => [...boardKeys.all, "overview"] as const,
  counts: (dateFrom = "", dateTo = "") =>
    [...boardKeys.all, "counts", dateFrom, dateTo] as const,
};

export const moKeys = {
  all: ["mo"] as const,
  detail: (code: string) => [...moKeys.all, "detail", code] as const,
  trace: (code: string) => [...moKeys.all, "trace", code] as const,
  events: (code: string) => [...moKeys.all, "events", code] as const,
};

export const catalogKeys = {
  lines: () => ["catalog", "lines"] as const,
  reasons: (group?: string) => ["catalog", "reasons", group ?? "all"] as const,
};

export const reportKeys = {
  all: ["reports"] as const,
  moProgress: (
    status?: string,
    dateFrom?: string,
    dateTo?: string,
    limit?: number,
    offset?: number,
  ) =>
    [
      ...reportKeys.all,
      "mo-progress",
      status ?? "all",
      dateFrom ?? "",
      dateTo ?? "",
      limit ?? PAGE_SIZE,
      offset ?? 0,
    ] as const,
  hourly: (bucket: number, dateFrom: string, dateTo: string) =>
    [...reportKeys.all, "hourly", bucket, dateFrom, dateTo] as const,
};
