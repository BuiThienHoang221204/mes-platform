"use client";

import { Warning } from "@/components/common/PhosphorIcons";
import { ScanBar } from "@/components/scan/ScanBar";
import { VIEW } from "@/constants/roles";
import { stationName } from "@/constants/stations";
import { useCanScanHere } from "@/hooks/useStationPerm";

export function StationScanArea({ station, hint }: { station: number; hint: string }) {
  const { perm, canScan } = useCanScanHere(station);

  if (canScan) return <ScanBar station={station} hint={hint} />;

  if (perm === VIEW) {
    return (
      <div className="flex items-start gap-3 rounded-card border border-line bg-surface-2 px-5 py-4 text-body text-fg-muted">
        <Warning size={24} className="shrink-0" />
        <span>Bạn chỉ xem được {stationName(station)}, không quét nhận và không bấm được gì.</span>
      </div>
    );
  }

  return (
    <div className="flex items-start gap-3 rounded-card border border-danger bg-danger-soft px-5 py-4 text-body text-danger">
      <Warning size={24} weight="fill" className="shrink-0" />
      <span>
        Bạn không thuộc phòng ban của {stationName(station)} nên không thao tác được ở đây.
      </span>
    </div>
  );
}
