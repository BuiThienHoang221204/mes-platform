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
};

export function AppButton({
  variant = "outline",
  size = "lg",
  block,
  icon,
  className = "",
  children,
  disabled,
  ...rest
}: Props) {
  return (
    <button
      {...rest}
      disabled={disabled}
      className={[
        "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-field border font-medium transition-colors",
        VARIANT[variant],
        SIZE[size],
        block ? "w-full" : "",
        disabled ? "cursor-not-allowed opacity-45" : "",
        className,
      ].join(" ")}
    >
      {icon ? <span className="flex shrink-0 items-center">{icon}</span> : null}
      {children}
    </button>
  );
}
