import type { ReactNode } from "react";

type Props = {
  icon?: ReactNode;
  title: string;
  hint?: string;
  action?: ReactNode;
};

export function EmptyState({ icon, title, hint, action }: Props) {
  return (
    <div className="flex flex-col items-center gap-3 px-6 py-12 text-center">
      {icon ? <span className="text-fg-subtle">{icon}</span> : null}
      <p className="text-body-lg text-fg-muted">{title}</p>
      {hint ? <p className="max-w-md text-body-sm text-fg-subtle">{hint}</p> : null}
      {action}
    </div>
  );
}
