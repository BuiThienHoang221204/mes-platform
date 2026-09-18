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
            className={`flex min-h-touch min-w-0 grow basis-[46%] items-center gap-2 rounded-field px-2.5 text-left sm:basis-0 sm:gap-3 sm:px-3 ${
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
              <span className="hidden truncate text-caption text-fg-subtle sm:block">{s.sub}</span>
            </span>
          </button>
        );
      })}
    </div>
  );
}
