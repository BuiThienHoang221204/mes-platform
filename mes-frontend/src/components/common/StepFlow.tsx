"use client";

import { STATION_STEPS, type StationStep } from "@/constants/stationSteps";

type Props = {
  station: number;
  active: string;
  onPick: (id: string) => void;
};

function StepButton({
  step,
  index,
  active,
  onPick,
}: {
  step: StationStep;
  index: number;
  active: boolean;
  onPick: (id: string) => void;
}) {
  return (
    <button
      type="button"
      onClick={() => onPick(step.id)}
      className={`flex min-h-touch min-w-0 grow basis-[46%] items-center gap-2 rounded-field px-2.5 text-left sm:basis-0 sm:gap-3 sm:px-3 ${
        active ? "bg-accent-soft text-accent" : "text-fg-muted hover:bg-surface-2"
      }`}
    >
      <span
        className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-pill text-caption tnum ${
          active ? "bg-accent text-accent-on" : "bg-surface-2 text-fg-muted"
        }`}
      >
        {index}
      </span>
      <span className="min-w-0">
        <span className="block truncate text-body font-medium">{step.name}</span>
        <span className="hidden truncate text-caption text-fg-subtle sm:block">{step.sub}</span>
      </span>
    </button>
  );
}

export function StepFlow({ station, active, onPick }: Props) {
  const flow = STATION_STEPS[station];
  if (!flow) return null;

  return (
    <div className="flex flex-wrap gap-1 rounded-card border border-line bg-surface p-1.5">
      {flow.steps.map((s, i) => (
        <StepButton key={s.id} step={s} index={i + 1} active={s.id === active} onPick={onPick} />
      ))}
    </div>
  );
}
