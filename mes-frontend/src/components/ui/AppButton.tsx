"use client";

import type { ButtonHTMLAttributes, ReactNode } from "react";

type Variant = "primary" | "ghost" | "danger" | "outline";
type Size = "lg" | "md" | "sm";

const VARIANT: Record<Variant, string> = {
  primary: "bg-accent text-accent-on border-accent hover:bg-accent-strong",
  outline: "bg-surface text-fg border-line-strong hover:border-fg-subtle",
  ghost: "bg-transparent text-fg-muted border-transparent hover:bg-surface-2 hover:text-fg",
  danger: "bg-danger text-danger-on border-danger",
};

const SIZE: Record<Size, string> = {
  lg: "min-h-[48px] px-6 text-button",
  md: "min-h-[40px] px-5 text-button",
  sm: "min-h-[34px] px-4 text-body-sm",
};

type Props = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: Variant;
  size?: Size;
  block?: boolean;
  icon?: ReactNode;
  compact?: boolean;
};

export function AppButton({
  variant = "outline",
  size = "lg",
  block,
  icon,
  compact,
  className = "",
  children,
  disabled,
  title,
  "aria-label": ariaLabel,
  ...rest
}: Props) {
  const iconOnly = Boolean(compact && icon);
  const asText = typeof children === "string" ? children : undefined;

  return (
    <button
      {...rest}
      disabled={disabled}
      title={title ?? (iconOnly ? asText : undefined)}
      aria-label={ariaLabel ?? (iconOnly ? asText : undefined)}
      className={[
        "items-center justify-center gap-2 whitespace-nowrap rounded-field border font-medium transition-colors",
        VARIANT[variant],
        SIZE[size],
        iconOnly ? "max-sm:gap-0 max-sm:px-2 sm:!px-2.5" : "inline-flex",
        block ? "w-full" : "",
        disabled ? "cursor-not-allowed opacity-45" : "",
        className,
      ].join(" ")}
    >
      {icon ? <span className="flex shrink-0 items-center">{icon}</span> : null}
      {iconOnly ? <span className="max-sm:hidden">{children}</span> : children}
    </button>
  );
}
