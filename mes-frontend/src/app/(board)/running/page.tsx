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
    <main className="space-y-6 px-8 py-8">
      <header className="flex flex-wrap items-center gap-4">
        <h1 className="text-h1">Bảng đang chạy</h1>
        <span className="flex items-center gap-2 text-body-sm text-fg-subtle">
          <ArrowsClockwise size={20} />
          tự làm mới mỗi 10 giây
        </span>
      </header>

      <div className="grid grid-cols-3 gap-3 sm:grid-cols-6">
        {STATIONS.map((s) => (
          <div key={s.no} className="rounded-card border border-line bg-surface px-4 py-3">
            <p className="text-caption text-fg-subtle">
              {s.no} · {s.name}
            </p>
            <p className="flex items-baseline gap-2">
              <span className="text-h2 tnum text-fg">{waiting(s.no)}</span>
              <span className="text-caption text-fg-subtle">chờ</span>
              <span
                className={`ml-auto text-h3 tnum ${holding(s.no) ? "text-accent" : "text-fg-subtle"}`}
              >
                {holding(s.no)}
              </span>
              <span className="text-caption text-fg-subtle">đang làm</span>
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
