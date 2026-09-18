import type { ReactNode } from "react";

type Props = {
  kicker: string;
  title: string;
  subtitle?: string;
  children?: ReactNode;
};

export function PageHeader({ kicker, title, subtitle, children }: Props) {
  return (
    <header className="mb-4 space-y-2 lg:mb-6">
      <span className="inline-flex items-center gap-2 rounded-field bg-accent-soft px-3 py-1 text-caption uppercase tracking-wider text-accent">
        {kicker}
      </span>
      <div className="flex flex-wrap items-center gap-3 sm:gap-4">
        <h1 className="text-h3 sm:text-h2">{title}</h1>
        {children ? <div className="flex flex-wrap gap-2 sm:ml-auto">{children}</div> : null}
      </div>
      {subtitle ? <p className="max-w-3xl text-body text-fg-muted">{subtitle}</p> : null}
    </header>
  );
}
