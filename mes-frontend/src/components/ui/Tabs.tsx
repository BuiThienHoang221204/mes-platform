"use client";

import { useId, useRef, useState, type ReactNode } from "react";

export type TabItem = {
  id: string;
  label: ReactNode;
  meta?: ReactNode;
  icon?: ReactNode;
  panel: ReactNode;
};

type Props = {
  tabs: TabItem[];
  initial?: string;
  actions?: ReactNode;
  className?: string;
};

export function Tabs({ tabs, initial, actions, className = "" }: Props) {
  const [active, setActive] = useState(initial ?? tabs[0]?.id);
  const base = useId();
  const bar = useRef<HTMLDivElement>(null);

  const at = Math.max(0, tabs.findIndex((t) => t.id === active));
  const here = tabs[at];

  const move = (to: number) => {
    const next = tabs[(to + tabs.length) % tabs.length];
    setActive(next.id);
    bar.current?.querySelector<HTMLButtonElement>(`#${CSS.escape(`${base}-tab-${next.id}`)}`)?.focus();
  };

  const onKey = (e: React.KeyboardEvent) => {
    if (e.key === "ArrowRight") move(at + 1);
    else if (e.key === "ArrowLeft") move(at - 1);
    else if (e.key === "Home") move(0);
    else if (e.key === "End") move(tabs.length - 1);
    else return;
    e.preventDefault();
  };

  return (
    <section className={`overflow-hidden rounded-card border border-line bg-surface ${className}`}>
      <div className="flex flex-wrap items-end gap-2 border-b border-line bg-surface-2 pl-2 pr-2 pt-2 sm:pr-3">
        <div ref={bar} role="tablist" onKeyDown={onKey} className="no-scrollbar flex min-w-0 flex-1 gap-1 overflow-x-auto">
          {tabs.map((t) => {
            const on = t.id === here?.id;
            return (
              <button
                key={t.id}
                id={`${base}-tab-${t.id}`}
                type="button"
                role="tab"
                aria-selected={on}
                aria-controls={`${base}-panel-${t.id}`}
                tabIndex={on ? 0 : -1}
                onClick={() => setActive(t.id)}
                className={`flex min-w-0 shrink-0 items-center gap-2 rounded-t-card px-3 py-2.5 text-body sm:px-4 ${
                  on
                    ? "-mb-px border border-b-0 border-line bg-surface font-semibold text-fg"
                    : "text-fg-muted hover:bg-surface-3 hover:text-fg"
                }`}
              >
                {t.icon ? <span className="shrink-0">{t.icon}</span> : null}
                <span className="truncate">{t.label}</span>
              </button>
            );
          })}
        </div>

        {here?.meta ? (
          <span className="hidden shrink-0 pb-3 text-caption text-fg-subtle sm:block">
            {here.meta}
          </span>
        ) : null}
        {actions ? <div className="shrink-0 pb-2">{actions}</div> : null}
      </div>

      {tabs.map((t) => (
        <div
          key={t.id}
          id={`${base}-panel-${t.id}`}
          role="tabpanel"
          aria-labelledby={`${base}-tab-${t.id}`}
          hidden={t.id !== here?.id}
          className="p-4 sm:p-5"
        >
          {t.panel}
        </div>
      ))}
    </section>
  );
}
