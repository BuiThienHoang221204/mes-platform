"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { StationPicker } from "@/components/station/StationPicker";
import { stationRoute } from "@/constants/stations";
import { useMyStation } from "@/hooks/useStationPerm";
import { useSessionStore } from "@/stores/useSessionStore";

export default function ScanEntry() {
  const router = useRouter();
  const checked = useSessionStore((s) => s.checked);
  const fullName = useSessionStore((s) => s.fullName);
  const { station, needsPick } = useMyStation();

  useEffect(() => {
    if (!checked) return;
    if (!fullName) router.replace("/login");
    else if (station != null) router.replace(stationRoute(station));
  }, [checked, fullName, station, router]);

  if (!checked || !fullName || station != null) return null;
  if (!needsPick) return null;

  return (
    <div className="mx-auto max-w-xl py-10">
      <StationPicker />
    </div>
  );
}
