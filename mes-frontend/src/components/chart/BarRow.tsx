import type { ReactNode } from "react";

/**
 * Một dòng thanh ngang: nhãn · rãnh nền có thanh · con số.
 *
 * Nằm ngang chứ không dựng đứng vì nhãn ở đây là mã lệnh 7 ký tự và tên trạm —
 * kê dưới cột dọc thì phải xoay chữ hoặc cắt bớt, mà thêm một dòng thì rẻ.
 *
 * `segments` cho phép xếp chồng nhiều đoạn trong cùng một rãnh. Khe 2px giữa hai
 * đoạn là MÀU NỀN chứ không phải viền: viền ăn thêm chiều rộng nên tổng các đoạn
 * không còn đúng tỷ lệ với nhau nữa.
 */
export type BarSegment = {
  value: number;
  color: string;
  label: string;
};

type Props = {
  label: ReactNode;
  sub?: ReactNode;
  segments: BarSegment[];
  /** Mẫu số để quy ra bề rộng. Cùng một `max` cho mọi dòng thì mới so được. */
  max: number;
  value: ReactNode;
  title?: string;
  /** Vạch mốc vuông góc, tính theo cùng thang với `max`. */
  marks?: { at: number; label: string; faint?: boolean }[];
  /** Mili giây chờ trước khi thanh chạy ra — để các dòng nối đuôi nhau. */
  delayMs?: number;
};

export function BarRow({
  label,
  sub,
  segments,
  max,
  value,
  title,
  marks = [],
  delayMs = 0,
}: Props) {
  const total = segments.reduce((n, s) => n + s.value, 0);
  const scale = max > 0 ? 100 / max : 0;

  return (
    <div className="grid grid-cols-[minmax(7rem,11rem)_1fr_auto] items-center gap-3" title={title}>
      <div className="min-w-0">
        <div className="truncate text-body-sm font-semibold text-fg">{label}</div>
        {sub ? <div className="truncate text-caption text-fg-subtle">{sub}</div> : null}
      </div>

      <div className="relative h-5 rounded-r-xs bg-surface-3">
        <div
          className="rise-x flex h-full overflow-hidden rounded-r-xs"
          style={{
            width: `${Math.min(100, total * scale)}%`,
            animationDelay: `${delayMs}ms`,
          }}
        >
          {segments
            .filter((s) => s.value > 0)
            .map((s, i) => (
              <span
                key={s.label}
                title={`${s.label}: ${s.value.toLocaleString("vi-VN")}`}
                className={`h-full ${i > 0 ? "ml-[2px]" : ""}`}
                style={{ flex: s.value, background: s.color }}
              />
            ))}
        </div>
        {marks.map((m) => (
          <span
            key={m.label}
            title={m.label}
            aria-hidden
            className={`absolute -top-0.5 -bottom-0.5 w-0.5 ${m.faint ? "bg-fg-subtle" : "bg-fg-muted"}`}
            style={{ left: `${Math.min(100, m.at * scale)}%` }}
          />
        ))}
      </div>

      <div className="whitespace-nowrap text-right text-body-sm tnum text-fg">{value}</div>
    </div>
  );
}
