import type { ReactNode } from "react";

import type { BarSegment } from "@/components/chart/BarRow";

export type Column = {
  key: string;
  label: ReactNode;
  sub?: ReactNode;
  /** Mỗi phần tử là MỘT cột con, đứng sát cạnh nhau trong cùng một nhóm. */
  segments: BarSegment[];
  title?: string;
};

type Props = {
  columns: Column[];
  /** Mẫu số chung cho mọi cột — có chung mẫu số thì mới so được nhóm này với nhóm kia. */
  max: number;
  /** Chiều cao vùng vẽ, tính bằng px. */
  height?: number;
  /** Bề ngang MỖI cột con, tính bằng px. */
  barWidth?: number;
};

/**
 * Cột dọc GOM NHÓM: mỗi hạng mục một nhóm, trong nhóm mỗi chuỗi một cột.
 *
 * Gom nhóm chỉ chịu được ít chuỗi. UK Government Analysis Function đặt trần **4 cột
 * mỗi cụm**; ở đây 2 chuỗi × 6 trạm = 12 cột, còn rộng chán. Cùng dạng này mà đem
 * cho biểu đồ ② thì vỡ ngay — 100 lệnh trong một khung giờ là 100 cột một cụm.
 *
 * Xếp cạnh nhau chứ không xếp chồng vì hai số này là hai câu hỏi khác nhau, không
 * phải hai phần của một tổng: "bao nhiêu việc chờ người đi quét" và "bao nhiêu việc
 * đang chạy". Cộng chúng lại thành một cột thì phải ước lượng độ dài từng đoạn mới
 * so được trạm này với trạm kia; để cạnh nhau thì cả hai cùng đứng trên một vạch chân.
 *
 * Cột bằng 0 vẫn phải THẤY được: vẽ vạch chân 2px thay vì bỏ trống, không thì người
 * xem không phân biệt nổi "trạm này rỗng" với "trạm này chưa có số liệu".
 *
 * `barWidth` tính bằng px chứ không phải tên lớp Tailwind: lớp dựng từ biến thì bộ quét
 * không thấy để sinh CSS, và cột biến mất mà không báo lỗi gì.
 */
const GROUP_STEP_MS = 80;
const BAR_STEP_MS = 40;
const LABEL_LAG_MS = 320;

export function ColumnChart({ columns, max, height = 180, barWidth = 56 }: Props) {
  const scale = max > 0 ? height / max : 0;

  return (
    <div className="flex items-end justify-around gap-3 overflow-x-auto pb-1">
      {columns.map((c, ci) => (
        <div key={c.key} title={c.title} className="flex flex-1 flex-col items-center">
          <div className="flex w-full items-end justify-center gap-0.5" style={{ height }}>
            {c.segments.map((s, si) => {
              const delay = ci * GROUP_STEP_MS + si * BAR_STEP_MS;
              return (
                <div key={s.label} className="flex h-full flex-col justify-end">
                  <span
                    className="fade-up mb-1 text-center text-body-sm tnum text-fg"
                    style={{ animationDelay: `${delay + LABEL_LAG_MS}ms` }}
                  >
                    {s.value}
                  </span>
                  <span
                    title={`${s.label}: ${s.value.toLocaleString("vi-VN")}`}
                    className="rise-y rounded-t-xs"
                    style={{
                      width: barWidth,
                      height: Math.max(2, s.value * scale),
                      background: s.value > 0 ? s.color : "var(--color-surface-3)",
                      animationDelay: `${delay}ms`,
                    }}
                  />
                </div>
              );
            })}
          </div>

          <div className="w-full border-t border-line pt-2 text-center">
            <div className="truncate text-body-sm font-semibold text-fg">{c.label}</div>
            {c.sub ? <div className="truncate text-caption text-fg-subtle">{c.sub}</div> : null}
          </div>
        </div>
      ))}
    </div>
  );
}
