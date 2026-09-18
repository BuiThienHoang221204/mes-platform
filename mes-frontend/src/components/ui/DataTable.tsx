"use client";

import { useEffect, useRef, type ReactNode } from "react";

export type Column = {
  label?: ReactNode;
  right?: boolean;
  className?: string;
  cellClassName?: string;
  /** Neo cột này vào mép PHẢI, không trôi đi khi cuộn ngang.
   *
   *  Dành cho cột nút bấm: bảng đang chạy có 12 cột nên cột nút nằm tít ngoài cùng,
   *  muốn bấm Dừng hay Hoàn thành là phải cuộn hết bảng rồi mới thấy. Neo lại thì
   *  thao tác luôn trong tầm tay, còn phần số liệu vẫn cuộn bình thường. */
  stickyRight?: boolean;
};

export type Row = {
  key: string;
  cells: ReactNode[];
  className?: string;
  selectable?: boolean;
};

type Selection = {
  picked: string[];
  onPick: (keys: string[]) => void;
};

type Props = {
  columns: Column[];
  rows: Row[];
  fill?: boolean;
  maxHeight?: string;
  pad?: "sm" | "md" | "lg";
  nowrap?: boolean;
  selection?: Selection;
};

const PAD = {
  sm: "px-2.5 py-2 sm:px-3 sm:py-2.5",
  md: "px-3 py-2.5 sm:px-4 sm:py-3",
  lg: "px-3 py-2.5 sm:px-5 sm:py-3",
} as const;

const HEAD =
  "sticky top-0 z-10 bg-surface-2 font-medium shadow-[inset_0_-1px_0_var(--color-line)]";

/* Bóng đổ về bên TRÁI để thấy rõ phần số liệu đang chui xuống dưới cột neo. Thiếu
   nó thì hai vùng dính liền nhau và mắt không biết chỗ nào đang cuộn. */
const STICKY = "sticky right-0 shadow-[-10px_0_10px_-10px_rgba(0,0,0,0.35)]";

const BOX = "h-5 w-5 shrink-0 cursor-pointer accent-[var(--color-accent)]";

function HeadBox({ all, some, onToggle }: { all: boolean; some: boolean; onToggle: () => void }) {
  const box = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (box.current) box.current.indeterminate = some && !all;
  }, [some, all]);

  return (
    <input
      ref={box}
      type="checkbox"
      className={BOX}
      checked={all}
      onChange={onToggle}
      aria-label={all ? "Bỏ chọn tất cả" : "Chọn tất cả"}
    />
  );
}

export function DataTable({
  columns,
  rows,
  fill,
  maxHeight,
  pad = "md",
  nowrap,
  selection,
}: Props) {
  const box = fill
    ? "overflow-auto lg:min-h-0 lg:flex-1"
    : maxHeight
      ? "overflow-auto"
      : "overflow-x-auto";
  const wrap = nowrap ? "whitespace-nowrap" : "whitespace-nowrap md:whitespace-normal";
  const p = PAD[pad];

  const pickable = rows.filter((r) => r.selectable !== false).map((r) => r.key);
  const picked = new Set(selection?.picked ?? []);
  const pickedHere = pickable.filter((k) => picked.has(k));
  const allPicked = pickable.length > 0 && pickedHere.length === pickable.length;

  const toggleAll = () => {
    if (!selection) return;
    const rest = selection.picked.filter((k) => !pickable.includes(k));
    selection.onPick(allPicked ? rest : [...rest, ...pickable]);
  };

  const toggleOne = (key: string) => {
    if (!selection) return;
    selection.onPick(
      picked.has(key)
        ? selection.picked.filter((k) => k !== key)
        : [...selection.picked, key],
    );
  };

  return (
    <div className={box} style={fill || !maxHeight ? undefined : { maxHeight }}>
      <table className={`w-full border-collapse ${wrap}`}>
        <thead>
          <tr className="text-left text-caption uppercase tracking-wider text-fg-subtle">
            {selection ? (
              <th scope="col" className={[HEAD, p, "w-px"].join(" ")}>
                <HeadBox
                  all={allPicked}
                  some={pickedHere.length > 0}
                  onToggle={toggleAll}
                />
              </th>
            ) : null}
            {columns.map((c, i) => (
              <th
                key={i}
                scope="col"
                className={[
                  HEAD,
                  p,
                  c.right ? "text-right" : "",
                  c.stickyRight ? `${STICKY} z-20` : "",
                  c.className ?? "",
                ].join(" ")}
              >
                {c.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => {
            const on = picked.has(r.key);
            return (
              <tr
                key={r.key}
                className={`border-b border-line last:border-b-0 ${
                  on ? "bg-accent-soft" : ""
                } ${r.className ?? ""}`}
              >
                {selection ? (
                  <td className={`${p} w-px`}>
                    {r.selectable === false ? null : (
                      <input
                        type="checkbox"
                        className={BOX}
                        checked={on}
                        onChange={() => toggleOne(r.key)}
                        aria-label={`Chọn ${r.key}`}
                      />
                    )}
                  </td>
                ) : null}
                {r.cells.map((cell, i) => (
                  <td
                    key={i}
                    className={[
                      p,
                      "text-body text-fg",
                      columns[i]?.right ? "text-right tnum" : "",
                      // Ô neo phải TỰ tô nền: nó nổi lên trên các ô khác, nền trong
                      // suốt thì chữ của cột bên dưới lòi qua.
                      columns[i]?.stickyRight
                        ? `${STICKY} ${on ? "bg-accent-soft" : "bg-surface"}`
                        : "",
                      columns[i]?.className ?? "",
                      columns[i]?.cellClassName ?? "",
                    ].join(" ")}
                  >
                    {cell}
                  </td>
                ))}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
