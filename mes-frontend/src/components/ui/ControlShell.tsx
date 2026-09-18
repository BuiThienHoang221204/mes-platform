import type { ReactNode } from "react";

export const controlBox = (label?: string, disabled?: boolean, className = "") =>
  [
    "flex items-center gap-2 rounded-field border border-line-strong bg-surface px-3 text-left",
    label ? "min-h-[48px]" : "min-h-[40px]",
    disabled ? "cursor-not-allowed opacity-45" : "",
    className,
  ].join(" ");

type Props = {
  label?: string;
  icon?: ReactNode;
  mono?: boolean;
  children: ReactNode;
};

export function ControlFace({ label, icon, mono, children }: Props) {
  const value = `block truncate ${mono ? "tnum " : ""}text-fg`;

  return (
    <>
      <span className="min-w-0 flex-1">
        {label ? (
          <span className="block truncate text-caption text-fg-subtle">{label}</span>
        ) : null}
        <span className={`${value} ${label ? "text-body" : "text-body-sm"}`}>{children}</span>
      </span>
      {icon ? <span className="shrink-0 text-fg-subtle">{icon}</span> : null}
    </>
  );
}
