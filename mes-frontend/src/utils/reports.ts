import type { HourlyReport } from "@/types/reports";

export type Tier = "low" | "mid" | "high";

export const TIER_COLOR: Record<Tier, string> = {
  low: "var(--color-tier-low)",
  mid: "var(--color-tier-mid)",
  high: "var(--color-tier-high)",
};

/** Ba bậc đạt định mức. Ranh giới ĐÓNG ở 100: đúng 100% là đạt, chưa phải vượt. */
export const tierOf = (rate: number, targetPct: number): Tier =>
  rate < targetPct ? "low" : rate <= 100 ? "mid" : "high";

export const tierLegend = (targetPct: number) => [
  { color: TIER_COLOR.low, label: `dưới ${targetPct}% · hụt` },
  { color: TIER_COLOR.mid, label: `${targetPct}–100% · đạt mục tiêu` },
  { color: TIER_COLOR.high, label: "trên 100% · vượt định mức" },
];

export type SlotRow = {
  code: string;
  qty: number;
  target: number;
  headcount: number | null;
  rate: number;
};

/** Gom báo cáo theo KHUNG GIỜ thay vì theo lệnh — trục của màn xếp hạng là lệnh.
 *
 *  Server trả `series[].points[]` vì đó là hình dạng rẻ nhất để gộp ở SQL. Màn này
 *  hỏi ngược lại: "khung giờ này có những lệnh nào". Lật một lần ở đây, không lật
 *  đi lật lại trong lúc vẽ.
 */
export function bySlot(report: HourlyReport | undefined) {
  const slots = new Map<string, SlotRow[]>();
  const ends = new Map<string, string>();
  if (!report) return { keys: [] as string[], slots, ends };

  for (const s of report.series) {
    for (const p of s.points) {
      ends.set(p.at, p.at_end);
      const rows = slots.get(p.at) ?? [];
      rows.push({
        code: s.code,
        qty: p.qty,
        target: p.target_qty,
        headcount: p.headcount,
        rate: p.target_qty > 0 ? (p.qty / p.target_qty) * 100 : 0,
      });
      slots.set(p.at, rows);
    }
  }
  for (const rows of slots.values()) rows.sort((a, b) => a.rate - b.rate);
  return { keys: [...slots.keys()].sort(), slots, ends };
}

const hhmm = (iso: string) => iso.slice(11, 16);

export const slotRange = (at: string, end: string | undefined) =>
  `${hhmm(at)}–${end ? hhmm(end) : "—"}`;

export const dayOf = (iso: string) => iso.slice(0, 10);

/** `2026-09-15` → `15/09`, để nhãn ngắn mà vẫn đọc được. */
export const shortDay = (iso: string) => `${iso.slice(8, 10)}/${iso.slice(5, 7)}`;

export const addDays = (iso: string, n: number) => {
  const d = new Date(`${iso}T00:00:00`);
  d.setDate(d.getDate() + n);
  return d.toISOString().slice(0, 10);
};
