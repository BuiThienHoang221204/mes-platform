"use client";

import type { ReactNode } from "react";

type Props = {
  selected: boolean;
  title: ReactNode;
  hint?: ReactNode;
  disabled?: boolean;
  onSelect: () => void;
};

/**
 * Một lựa chọn phải bấm rõ ràng, kiểu radio. Dùng ở những chỗ KHÔNG được có mặc
 * định im lặng — thao tác không hoàn tác được thì người dùng phải nói ra mình
 * chọn đường nào, chứ không phải bấm tiếp rồi hệ thống tự hiểu.
 */
export function ChoiceCard({ selected, title, hint, disabled, onSelect }: Props) {
  return (
    <button
      type="button"
      disabled={disabled}
      onClick={onSelect}
      className={`flex w-full gap-3 rounded-field border px-4 py-3 text-left disabled:opacity-45 ${
        selected ? "border-2 border-accent bg-accent-soft" : "border-line-strong bg-surface hover:border-accent-line"
      }`}
    >
      <span
        className={`mt-1 h-4 w-4 shrink-0 rounded-pill border-2 ${
          selected ? "border-[6px] border-accent" : "border-line-strong"
        }`}
      />
      <span className="min-w-0">
        <span className="block text-body font-medium text-fg">{title}</span>
        {hint ? <span className="block text-body-sm text-fg-muted">{hint}</span> : null}
      </span>
    </button>
  );
}
