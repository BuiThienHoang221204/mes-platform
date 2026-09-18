"use client";

import { CheckCircle } from "@/components/common/PhosphorIcons";
import { AppCard } from "@/components/ui/AppCard";
import { STATIONS, stationName } from "@/constants/stations";
import { useMyStation } from "@/hooks/useStationPerm";
import { useStationStore } from "@/stores/useStationStore";

export function StationPicker({ compact }: { compact?: boolean }) {
  const { own, station } = useMyStation();
  const setPicked = useStationStore((s) => s.setPicked);

  const body = (
    <div className="grid gap-2 sm:grid-cols-2">
      {STATIONS.filter((s) => own.includes(s.no)).map((s) => {
        const active = station === s.no;
        return (
          <button
            key={s.no}
            type="button"
            onClick={() => setPicked(s.no)}
            className={`flex min-h-touch items-center gap-3 rounded-field border px-3 text-left sm:px-4 ${
              active ? "border-accent bg-accent-soft" : "border-line-strong bg-surface"
            }`}
          >
            <span
              className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-pill text-body-sm tnum ${
                active ? "bg-accent text-accent-on" : "bg-surface-2 text-fg-muted"
              }`}
            >
              {s.no}
            </span>
            <span className={`min-w-0 flex-1 truncate text-body ${active ? "text-accent" : "text-fg"}`}>
              {stationName(s.no)}
            </span>
            {active ? <CheckCircle size={22} weight="fill" className="shrink-0 text-accent" /> : null}
          </button>
        );
      })}
    </div>
  );

  if (compact) return body;

  return (
    <AppCard title="Bạn đang làm ở trạm nào?" meta="chọn một lần, đổi lúc nào cũng được">
      <div className="space-y-4">
        <p className="text-body text-fg-muted">
          Vai của bạn thao tác được nhiều trạm, nên hệ thống không tự đoán được cú quét ăn vào bước
          nào. Chọn trạm bạn đang đứng thì quét mới ghi đúng sổ.
        </p>
        {body}
      </div>
    </AppCard>
  );
}
