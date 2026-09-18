"use client";

import { forwardRef, type SelectHTMLAttributes } from "react";

import { CaretDown } from "@/components/common/PhosphorIcons";

type Option = { value: string | number; label: string };

type Props = SelectHTMLAttributes<HTMLSelectElement> & {
  label?: string;
  hint?: string;
  error?: string;
  options: Option[];
  placeholder?: string;
};

export const AppSelect = forwardRef<HTMLSelectElement, Props>(function AppSelect(
  { label, hint, error, options, placeholder, className = "", id, ...rest },
  ref,
) {
  const selectId = id ?? rest.name;
  return (
    <div className="space-y-1.5">
      {label ? (
        <label htmlFor={selectId} className="block text-label text-fg-muted">
          {label}
        </label>
      ) : null}

      <div className="relative">
        <select
          {...rest}
          id={selectId}
          ref={ref}
          aria-invalid={error ? true : undefined}
          className={[
            "min-h-touch w-full appearance-none rounded-field border bg-surface px-4 pr-12 text-body-lg text-fg",
            error ? "border-danger" : "border-line-strong",
            className,
          ].join(" ")}
        >
          {placeholder ? (
            <option value="" disabled>
              {placeholder}
            </option>
          ) : null}
          {options.map((o) => (
            <option key={o.value} value={o.value}>
              {o.label}
            </option>
          ))}
        </select>
        <CaretDown
          size={24}
          className="pointer-events-none absolute inset-y-0 right-4 my-auto text-fg-subtle"
        />
      </div>

      {error ? (
        <p className="text-body-sm text-danger">{error}</p>
      ) : hint ? (
        <p className="text-body-sm text-fg-subtle">{hint}</p>
      ) : null}
    </div>
  );
});
