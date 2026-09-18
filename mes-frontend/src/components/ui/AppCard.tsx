import type { ReactNode } from "react";

type Props = {
  title?: ReactNode;
  meta?: ReactNode;
  actions?: ReactNode;
  flush?: boolean;
  className?: string;
  bodyClassName?: string;
  children: ReactNode;
};

export function AppCard({
  title,
  meta,
  actions,
  flush,
  className = "",
  bodyClassName = "",
  children,
}: Props) {
  return (
    <section className={`overflow-hidden rounded-card border border-line bg-surface ${className}`}>
      {title || actions ? (
        <header className="flex flex-wrap items-center gap-3 border-b border-line bg-surface-2 px-5 py-3">
          <h2 className="shrink-0 text-title">{title}</h2>
          {meta ? (
            <span className="min-w-0 flex-1 truncate text-caption text-fg-subtle">{meta}</span>
          ) : null}
          {actions ? (
            <div className="ml-auto flex shrink-0 flex-wrap items-center gap-2">{actions}</div>
          ) : null}
        </header>
      ) : null}
      <div className={`${flush ? "" : "p-5"} ${bodyClassName}`}>{children}</div>
    </section>
  );
}
