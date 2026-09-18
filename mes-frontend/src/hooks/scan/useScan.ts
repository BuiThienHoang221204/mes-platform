"use client";

import { useMutation } from "@tanstack/react-query";

import { stationService } from "@/services/station.service";
import { useInvalidateStation } from "@/hooks/useInvalidateStation";
import { useMyStation } from "@/hooks/useStationPerm";
import { useScanStore } from "@/stores/useScanStore";
import { useUiStore } from "@/stores/useUiStore";
import type { ApiError } from "@/types/api";

export function useScan(station: number) {
  const { needsPick } = useMyStation();
  const setResult = useScanStore((s) => s.setResult);
  const setError = useScanStore((s) => s.setError);
  const toast = useUiStore((s) => s.toast);
  const invalidate = useInvalidateStation();

  return useMutation({
    mutationFn: (raw: string) => stationService.scan(raw, needsPick ? station : null),
    onSuccess: (r) => {
      setResult(station, r);
      invalidate(r.mo_code);
      toast(r.duplicate ? `${r.mo_code} — đã nhận rồi` : r.message, r.duplicate ? "warn" : "ok");
    },
    onError: (e: ApiError) => {
      setError(station, e.message);
      toast(e.message, "danger");
    },
  });
}
