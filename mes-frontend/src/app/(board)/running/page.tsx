"use client";

import { RunningTable } from "@/components/board/RunningTable";
import { ArrowsClockwise } from "@/components/common/PhosphorIcons";
import { useCounts } from "@/hooks/board/useBoard";
import { STATIONS } from "@/constants/stations";

export default function RunningBoardPage() {
  const { data } = useCounts();
  const waiting = (n: number) => data?.counts?.[String(n)] ?? 0;
  const holding = (n: number) => data?.holding?.[String(n)] ?? 0;

  return (
    <main className="space-y-4 px-3 pb-4 pt-[calc(1rem+env(safe-area-inset-top))] sm:px-6 sm:py-6 lg:space-y-6 lg:px-8 lg:py-8">
      <header className="flex flex-wrap items-center gap-x-4 gap-y-1">
        <h1 className="text-h2 sm:text-h1">Bảng đang chạy</h1>
        <span className="flex items-center gap-2 text-body-sm text-fg-subtle">
          <ArrowsClockwise size={20} />
          tự làm mới mỗi 10 giây
        </span>
      </header>

      <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 sm:gap-3 lg:grid-cols-6">
        {STATIONS.map((s) => (
          <div key={s.no} className="rounded-card border border-line bg-surface px-3 py-2.5 sm:px-4 sm:py-3">
            <p className="text-caption text-fg-subtle">
              {s.no} · {s.name}
            </p>
            <p className="mt-0.5 flex flex-wrap items-baseline justify-between gap-x-3">
              <span className="flex items-baseline gap-1.5">
                <span className="text-h3 tnum text-fg sm:text-h2">{waiting(s.no)}</span>
                <span className="text-caption text-fg-subtle">chờ</span>
              </span>
              <span className="flex items-baseline gap-1.5">
                <span
                  className={`text-title tnum sm:text-h3 ${holding(s.no) ? "text-accent" : "text-fg-subtle"}`}
                >
                  {holding(s.no)}
                </span>
                <span className="text-caption text-fg-subtle">đang làm</span>
              </span>
            </p>
          </div>
        ))}
      </div>

      <div className="rounded-card border border-line bg-surface">
        <RunningTable withActions />
      </div>
    </main>
  );
}
