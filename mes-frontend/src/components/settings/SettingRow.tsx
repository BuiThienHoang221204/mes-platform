import type { ReactNode } from "react";

type Props = {
  label: string;
  hint?: ReactNode;
  children: ReactNode;
};

export function SettingRow({ label, hint, children }: Props) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-4 border-b border-line py-5 first:pt-0 last:border-b-0 last:pb-0">
      <div className="min-w-56 flex-1">
        <div className="text-body-lg text-fg">{label}</div>
        {hint ? <p className="mt-1 max-w-xl text-body-sm text-fg-muted">{hint}</p> : null}
      </div>
      <div className="shrink-0">{children}</div>
    </div>
  );
}
