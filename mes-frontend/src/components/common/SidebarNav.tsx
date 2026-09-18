"use client";

import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";
import { useEffect, useId, useState, type ReactNode } from "react";

import { CaretDown } from "@/components/common/PhosphorIcons";

export type NavItem = {
  href: string;
  label: string;
  icon?: ReactNode;
  count?: number | null;
  viewOnly?: boolean;
  index?: number;
  children?: NavItem[];
};

type Match = (href: string) => boolean;

const ROW = "flex min-h-12 w-full items-center gap-3 rounded-field px-3 text-body";
const ON = "bg-accent-soft text-accent";
const OFF = "text-fg-muted hover:bg-surface-2 hover:text-fg";

function NavLink({ item, active }: { item: NavItem; active: boolean }) {
  return (
    <Link href={item.href} className={`${ROW} ${active ? ON : OFF}`}>
      {item.index != null ? (
        <span
          className={`w-4 shrink-0 text-center text-body-sm tnum ${
            active ? "text-accent" : "text-fg-subtle"
          }`}
        >
          {item.index}
        </span>
      ) : null}
      {item.icon ? <span className="shrink-0">{item.icon}</span> : null}
      <span className="min-w-0 flex-1 truncate">{item.label}</span>
      {item.viewOnly ? (
        <span className="shrink-0 rounded-field border border-line px-2 py-0.5 text-caption text-fg-subtle">
          chỉ xem
        </span>
      ) : null}
      {item.count != null ? (
        <span
          className={`min-w-7 shrink-0 rounded-pill px-2 py-0.5 text-center text-caption tnum ${
            active ? "bg-accent text-accent-on" : "bg-surface-2 text-fg-muted"
          }`}
        >
          {item.count}
        </span>
      ) : null}
    </Link>
  );
}

function NavBranch({ item, match }: { item: NavItem; match: Match }) {
  const kids = item.children ?? [];
  const hasActive = kids.some((k) => match(k.href));
  const [open, setOpen] = useState(hasActive);
  const panelId = useId();

  useEffect(() => {
    if (hasActive) setOpen(true);
  }, [hasActive]);

  return (
    <div>
      <button
        type="button"
        aria-expanded={open}
        aria-controls={panelId}
        onClick={() => setOpen((v) => !v)}
        className={`${ROW} ${hasActive && !open ? ON : OFF} text-left`}
      >
        {item.icon ? <span className="shrink-0">{item.icon}</span> : null}
        <span className="min-w-0 flex-1 truncate">{item.label}</span>
        <CaretDown
          size={18}
          aria-hidden
          className={`shrink-0 transition-transform duration-200 ${open ? "rotate-180" : ""}`}
        />
      </button>

      <div id={panelId} className="drawer grid" data-open={open ? "" : undefined}>
        <div className="overflow-hidden">
          <div className="mt-1 ml-5 space-y-1 border-l border-line pl-2">
            {kids.map((k) => (
              <NavLink key={k.href} item={k} active={match(k.href)} />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

export function NavGroup({ title, items }: { title: string; items: NavItem[] }) {
  const pathname = usePathname();
  const params = useSearchParams();

  const match: Match = (href) => {
    const [base, query] = href.split("?");
    if (!query) return pathname === base && !params.get("step");
    return pathname === base && params.get("step") === new URLSearchParams(query).get("step");
  };

  if (!items.length) return null;

  return (
    <div className="space-y-1">
      <p className="px-3 pb-1.5 text-caption uppercase tracking-wider text-fg-subtle">{title}</p>
      {items.map((it) =>
        it.children?.length ? (
          <NavBranch key={it.href} item={it} match={match} />
        ) : (
          <NavLink key={it.href} item={it} active={match(it.href)} />
        ),
      )}
    </div>
  );
}
