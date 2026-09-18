"use client";

import { ArrowLeft } from "@/components/common/PhosphorIcons";

const KEYS = ["1", "2", "3", "4", "5", "6", "7", "8", "9"];

type Props = {
  value: string;
  onChange: (next: string) => void;
  maxLength?: number;
  disabled?: boolean;
};

export function PinPad({ value, onChange, maxLength = 6, disabled }: Props) {
  const push = (d: string) => {
    if (value.length >= maxLength) return;
    onChange(value + d);
  };

  const key =
    "flex min-h-touch items-center justify-center rounded-field border border-line-strong bg-surface text-h3 text-fg active:bg-surface-2 disabled:opacity-45";

  return (
    <div className="space-y-4">
      <div className="flex justify-center gap-3" aria-hidden>
        {Array.from({ length: maxLength }, (_, i) => (
          <span
            key={i}
            className={`h-4 w-4 rounded-pill border ${
              i < value.length ? "border-accent bg-accent" : "border-line-strong bg-transparent"
            }`}
          />
        ))}
      </div>

      <div className="grid grid-cols-3 gap-3">
        {KEYS.map((d) => (
          <button key={d} type="button" className={key} disabled={disabled} onClick={() => push(d)}>
            {d}
          </button>
        ))}
        <button
          type="button"
          className={key}
          disabled={disabled || !value}
          onClick={() => onChange("")}
        >
          <span className="text-body">Xoá</span>
        </button>
        <button type="button" className={key} disabled={disabled} onClick={() => push("0")}>
          0
        </button>
        <button
          type="button"
          className={key}
          disabled={disabled || !value}
          onClick={() => onChange(value.slice(0, -1))}
          aria-label="Xoá một số"
        >
          <ArrowLeft size={28} weight="bold" />
        </button>
      </div>
    </div>
  );
}
