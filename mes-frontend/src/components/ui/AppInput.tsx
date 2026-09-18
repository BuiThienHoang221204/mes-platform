"use client";

import { forwardRef, type InputHTMLAttributes, type ReactNode } from "react";

type Props = InputHTMLAttributes<HTMLInputElement> & {
  label?: string;
  hint?: string;
  error?: string;
  mono?: boolean;
  trailing?: ReactNode;
};

export const AppInput = forwardRef<HTMLInputElement, Props>(function AppInput(
  { label, hint, error, mono, trailing, className = "", id, ...rest },
  ref,
) {
  const inputId = id ?? rest.name;

  // Không ô số nào trong MES nhận giá trị âm: sản lượng, số người, số thùng, quy
  // cách — âm là vô nghĩa với cả bốn. Chặn ở đây thay vì nhớ gắn `min` cho từng
  // ô, và vẫn cho phép ghi đè nếu sau này có ô thật sự cần số âm.
  const guarded =
    rest.type === "number" && rest.min === undefined ? { ...rest, min: 0 } : rest;

  return (
    <div className="space-y-1.5">
      {label ? (
        <label htmlFor={inputId} className="block text-label text-fg-muted">
          {label}
        </label>
      ) : null}

      <div className="relative">
        <input
          {...guarded}
          id={inputId}
          ref={ref}
          aria-invalid={error ? true : undefined}
          className={[
            "min-h-touch w-full rounded-field border bg-surface px-4 text-body-lg text-fg",
            "placeholder:text-fg-subtle",
            mono ? "font-mono tracking-wide" : "",
            error ? "border-danger" : "border-line-strong",
            trailing ? "pr-14" : "",
            className,
          ].join(" ")}
        />
        {trailing ? (
          <span className="absolute inset-y-0 right-3 flex items-center">{trailing}</span>
        ) : null}
      </div>

      {error ? (
        <p className="text-body-sm text-danger">{error}</p>
      ) : hint ? (
        <p className="text-body-sm text-fg-subtle">{hint}</p>
      ) : null}
    </div>
  );
});
