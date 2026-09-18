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
      className={`flex shrink-0 flex-wrap items-center justify-between gap-2 border-t border-line px-4 py-3 sm:gap-3 sm:px-5 ${className ?? ""}`}
    >
      <span className="order-first w-full text-center text-body-sm tnum text-fg-muted sm:order-none sm:w-auto">
        {offset + 1}–{offset + shown} / {total}
        {unit ? ` ${unit}` : ""}
      </span>
      <AppButton
        size="md"
        className="flex-1 sm:order-first sm:flex-none"
        disabled={offset === 0}
        onClick={() => onOffset(Math.max(0, offset - limit))}
      >
        Trang trước
      </AppButton>
      <AppButton
        size="md"
        className="flex-1 sm:flex-none"
        disabled={offset + shown >= total}
        onClick={() => onOffset(offset + limit)}
      >
        Trang sau
      </AppButton>
    </div>
  );
}
