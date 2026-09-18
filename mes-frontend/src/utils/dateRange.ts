export type DateRange = { from: string; to: string };

export type RangePreset =
  | "today"
  | "yesterday"
  | "last7"
  | "thisMonth"
  | "lastMonth"
  | "custom";

export const PRESET_LABEL: Record<RangePreset, string> = {
  today: "Hôm nay",
  yesterday: "Hôm qua",
  last7: "7 ngày trước",
  thisMonth: "Tháng này",
  lastMonth: "Tháng trước",
  custom: "Tuỳ chỉnh",
};

export const PRESETS: RangePreset[] = [
  "today",
  "yesterday",
  "last7",
  "thisMonth",
  "lastMonth",
  "custom",
];

/**
 * `yyyy-mm-dd` theo giờ MÁY, không qua `toISOString()`.
 *
 * `toISOString()` đổi sang UTC trước khi cắt chuỗi, nên ở múi giờ +07 mọi mốc trước
 * 07:00 sáng lùi về hôm trước. Lọc "Hôm nay" lúc 6 giờ sáng sẽ ra ngày hôm qua.
 */
const iso = (d: Date) =>
  `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(
    d.getDate(),
  ).padStart(2, "0")}`;

const shift = (d: Date, days: number) => {
  const x = new Date(d);
  x.setDate(x.getDate() + days);
  return x;
};

const monthStart = (d: Date, delta = 0) => new Date(d.getFullYear(), d.getMonth() + delta, 1);
const monthEnd = (d: Date, delta = 0) => new Date(d.getFullYear(), d.getMonth() + delta + 1, 0);

export function rangeOf(preset: RangePreset, now = new Date()): DateRange | null {
  switch (preset) {
    case "today":
      return { from: iso(now), to: iso(now) };
    case "yesterday":
      return { from: iso(shift(now, -1)), to: iso(shift(now, -1)) };
    case "last7":
      return { from: iso(shift(now, -6)), to: iso(now) };
    case "thisMonth":
      return { from: iso(monthStart(now)), to: iso(now) };
    case "lastMonth":
      return { from: iso(monthStart(now, -1)), to: iso(monthEnd(now, -1)) };
    case "custom":
      return null;
  }
}

/** `2026-09-17` → `17/09/2026`. */
export const dmy = (v: string) => (v ? v.split("-").reverse().join("/") : "");

export const rangeLabel = (r: DateRange) =>
  !r.from && !r.to
    ? "Tất cả"
    : r.from === r.to
      ? dmy(r.from)
      : `${dmy(r.from) || "…"} - ${dmy(r.to) || "…"}`;
