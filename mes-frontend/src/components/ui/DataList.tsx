import type { ReactNode } from "react";

export type DataRow = {
  k: ReactNode;
  v: ReactNode;
  tone?: "plain" | "warn" | "total";
};

/**
 * Bảng đối chiếu nhãn / số, canh phải, chữ số đều bề ngang. Dùng ở mọi chỗ cần
 * người đọc cộng trừ bằng mắt — sổ đóng thùng, chốt sổ, đối soát giờ.
 */
export function DataList({ rows, className = "" }: { rows: DataRow[]; className?: string }) {
  return (
    <dl className={`rounded-field bg-surface-2 px-4 py-3 text-body-sm ${className}`}>
      {rows.map((r, i) => (
        <div
          key={i}
          className={`flex justify-between gap-4 py-1 ${
            r.tone === "total" ? "mt-1.5 border-t border-line-strong pt-2.5 font-medium" : ""
          }`}
        >
          <dt className={r.tone === "warn" ? "text-warn" : "text-fg-muted"}>{r.k}</dt>
          <dd className={`tnum ${r.tone === "warn" ? "text-warn" : "text-fg"}`}>{r.v}</dd>
        </div>
      ))}
    </dl>
  );
}
