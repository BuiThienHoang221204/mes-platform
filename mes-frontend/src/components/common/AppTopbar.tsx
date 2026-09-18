"use client";

import { usePathname, useSearchParams } from "next/navigation";

import { CaretRight, List } from "@/components/common/PhosphorIcons";
import { FactoryClock } from "@/components/common/FactoryClock";
import { ThemeToggle } from "@/components/common/ThemeToggle";
import { PLANNER_STEPS } from "@/constants/plannerSteps";
import { stepsOf } from "@/constants/stationSteps";
import { STATIONS } from "@/constants/stations";

function useCrumb(): string[] {
  const pathname = usePathname();
  const params = useSearchParams();
  const step = params.get("step");

  if (pathname === "/mos") {
    const s = PLANNER_STEPS.find((x) => x.id === (step ?? PLANNER_STEPS[0].id));
    return ["Planner · Điều độ", s?.name ?? ""];
  }
  if (pathname.startsWith("/mos/")) return ["Tra cứu", "Truy cứu lệnh"];
  if (pathname === "/running") return ["Xem chung", "Bảng đang chạy"];
  if (pathname === "/trace") return ["Tra cứu", "Truy cứu lệnh"];
  if (pathname === "/flow") return ["Xem chung", "Luồng toàn quy trình"];

  const st = STATIONS.find((s) => s.route === pathname);
  if (st) {
    const steps = stepsOf(st.no);
    const cur = steps.find((x) => x.id === (step ?? steps[0]?.id));
    return [`Trạm ${st.no} · ${st.name}`, cur?.name ?? ""];
  }
  return [];
}

type Props = {
  onMenu?: () => void;
};

const ICON_BTN =
  "flex h-11 w-11 shrink-0 items-center justify-center rounded-field text-fg-muted hover:bg-surface-2 hover:text-fg";

export function AppTopbar({ onMenu }: Props) {
  const crumb = useCrumb();

  return (
    <header className="sticky top-0 z-30 flex shrink-0 items-center gap-2 border-b border-line bg-surface px-2 pb-3 pt-[calc(0.75rem+env(safe-area-inset-top))] sm:px-4 lg:static lg:z-auto lg:gap-3 lg:px-6 lg:py-2.5">
      <button
        type="button"
        onClick={onMenu}
        aria-label="Mở điều hướng"
        className={`${ICON_BTN} lg:hidden`}
      >
        <List size={26} />
      </button>

      <nav className="flex min-w-0 flex-1 items-center gap-2 text-body-sm">
        {crumb.map((c, i) => (
          <span
            key={c}
            className={`min-w-0 items-center gap-2 ${
              i === crumb.length - 1 ? "flex" : "hidden sm:flex"
            }`}
          >
            {i > 0 ? <CaretRight size={16} className="hidden shrink-0 text-fg-subtle sm:block" /> : null}
            <span className={i === crumb.length - 1 ? "truncate text-fg" : "truncate text-fg-subtle"}>
              {c}
            </span>
          </span>
        ))}
      </nav>

      <div className="flex shrink-0 items-center gap-1 sm:gap-2">
        <FactoryClock />
        <ThemeToggle />
      </div>
    </header>
  );
}
