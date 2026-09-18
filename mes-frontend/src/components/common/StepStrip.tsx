"use client";

import type { StationStep } from "@/constants/stationSteps";

type Props = {
  steps: StationStep[];
  active: string;
  onPick: (id: string) => void;
};

export function StepStrip({ steps, active, onPick }: Props) {
  return (
    <div className="flex flex-wrap gap-1 rounded-card border border-line bg-surface p-1.5">
      {steps.map((s, i) => {
        const on = s.id === active;
        return (
          <button
            key={s.id}
            type="button"
            onClick={() => onPick(s.id)}
            className={`flex min-h-touch min-w-0 flex-1 items-center gap-3 rounded-field px-3 text-left ${
              on ? "bg-accent-soft text-accent" : "text-fg-muted hover:bg-surface-2"
            }`}
          >
            <span
              className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-pill text-caption tnum ${
                on ? "bg-accent text-accent-on" : "bg-surface-2 text-fg-muted"
              }`}
            >
              {i + 1}
            </span>
            <span className="min-w-0">
              <span className="block truncate text-body font-medium">{s.name}</span>
              <span className="block truncate text-caption text-fg-subtle">{s.sub}</span>
            </span>
          </button>
        );
      })}
    </div>
  );
}
