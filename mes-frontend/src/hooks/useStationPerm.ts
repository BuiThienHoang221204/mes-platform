"use client";

import { FULL, ownStations, permissionFor, type Perm } from "@/constants/roles";
import { useSessionStore } from "@/stores/useSessionStore";
import { useStationStore } from "@/stores/useStationStore";

export function useStationPerm(station: number): Perm {
  const roles = useSessionStore((s) => s.roles);
  return permissionFor(roles, station);
}

export function useMyStation() {
  const roles = useSessionStore((s) => s.roles);
  const picked = useStationStore((s) => s.picked);
  const own = ownStations(roles);
  const needsPick = own.length > 1;
  const station = needsPick ? (picked != null && own.includes(picked) ? picked : null) : (own[0] ?? null);
  return { own, needsPick, station, ready: station != null };
}

export function useCanScanHere(station: number) {
  const perm = useStationPerm(station);
  return { perm, canScan: perm === FULL };
}
