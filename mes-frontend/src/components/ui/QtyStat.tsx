import type { ReactNode } from "react";

type Tone = "plain" | "accent" | "ok" | "warn" | "danger";

const TONE: Record<Tone, string> = {
  plain: "text-fg",
  accent: "text-accent",
  ok: "text-ok",
  warn: "text-warn",
  danger: "text-danger",
};

type Props = {
  label: string;
  value: number | string;
  unit?: string;
  hint?: ReactNode;
  tone?: Tone;
};

export function QtyStat({ label, value, unit, hint, tone = "plain" }: Props) {
  const shown = typeof value === "number" ? value.toLocaleString("vi-VN") : value;
  return (
    <div className="rounded-card border border-line bg-surface px-4 py-3 sm:px-5 sm:py-4">
      <div className="text-caption text-fg-subtle">{label}</div>
      <div className={`mt-1 text-h3 tnum sm:text-h2 ${TONE[tone]}`}>
        {shown}
        {unit ? <span className="ml-1 text-body text-fg-subtle">{unit}</span> : null}
      </div>
      {hint ? <div className="mt-1 text-caption text-fg-muted">{hint}</div> : null}
    </div>
  );
}
