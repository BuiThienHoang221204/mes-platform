"use client";

import { AppButton } from "@/components/ui/AppButton";

type Props = {
  offset: number;
  shown: number;
  total: number;
  limit: number;
  onOffset: (n: number) => void;
  unit?: string;
  className?: string;
};

export function Pager({ offset, shown, total, limit, onOffset, unit, className }: Props) {
  if (total <= shown && offset === 0) return null;

  return (
    <div
      className={`flex shrink-0 items-center justify-between gap-3 border-t border-line px-5 py-3 ${className ?? ""}`}
    >
      <AppButton size="md" disabled={offset === 0} onClick={() => onOffset(Math.max(0, offset - limit))}>
        Trang trước
      </AppButton>
      <span className="text-body-sm tnum text-fg-muted">
        {offset + 1}–{offset + shown} / {total}
        {unit ? ` ${unit}` : ""}
      </span>
      <AppButton
        size="md"
        disabled={offset + shown >= total}
        onClick={() => onOffset(offset + limit)}
      >
        Trang sau
      </AppButton>
    </div>
  );
}
