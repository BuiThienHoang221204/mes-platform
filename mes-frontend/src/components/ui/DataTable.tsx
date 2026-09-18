"use client";

import { useEffect, useRef, type ReactNode } from "react";

export type Column = {
  label?: ReactNode;
  right?: boolean;
  className?: string;
  cellClassName?: string;
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
  sm: "px-3 py-2.5",
  md: "px-4 py-3",
  lg: "px-5 py-3",
} as const;

const HEAD =
  "sticky top-0 z-10 bg-surface-2 font-medium shadow-[inset_0_-1px_0_var(--color-line)]";

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
    ? "min-h-0 flex-1 overflow-auto"
    : maxHeight
      ? "overflow-auto"
      : "overflow-x-auto";
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
      <table className={`w-full border-collapse ${nowrap ? "whitespace-nowrap" : ""}`}>
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
                className={[HEAD, p, c.right ? "text-right" : "", c.className ?? ""].join(" ")}
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
