/**
 * R2 — Query key CHỈ lấy từ đây. Gõ tay ở hai chỗ thì `invalidateQueries`
 * trượt, và nó trượt IM LẶNG, không báo lỗi gì.
 */
export const boardKeys = {
  all: ["board"] as const,
  running: () => [...boardKeys.all, "running"] as const,
  queue: (station: number) => [...boardKeys.all, "queue", station] as const,
  atStation: (station: number) => [...boardKeys.all, "at", station] as const,
  counts: () => [...boardKeys.all, "counts"] as const,
};

export const moKeys = {
  all: ["mo"] as const,
  detail: (code: string) => [...moKeys.all, "detail", code] as const,
  trace: (code: string) => [...moKeys.all, "trace", code] as const,
};

export const catalogKeys = {
  lines: () => ["catalog", "lines"] as const,
  reasons: (group?: string) => ["catalog", "reasons", group ?? "all"] as const,
};
