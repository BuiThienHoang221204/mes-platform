"use client";

import { useMutation } from "@tanstack/react-query";
import { stationService } from "@/services/station.service";
import { useInvalidateStation } from "@/hooks/useInvalidateStation";
import { useUiStore } from "@/stores/useUiStore";
import type { ApiError } from "@/types/api";
import { WI_OUTCOME } from "@/constants/status";

/** Ba thao tác trạm đã nối API. Trạm 1 và 3 KHÔNG có ở đây — chúng không có việc gì để làm. */
export function useHandover() {
  const invalidate = useInvalidateStation();
  const toast = useUiStore((s) => s.toast);
  return useMutation({
    mutationFn: (arg: string | { code: string; note?: string | null }) => {
      const code = typeof arg === "string" ? arg : arg.code;
      const note = typeof arg === "string" ? undefined : arg.note;
      return stationService.handover(code, note);
    },
    onSuccess: (r, arg) => {
      const code = typeof arg === "string" ? arg : arg.code;
      invalidate(code);
      toast(r.message);
    },
    onError: (e: ApiError) => toast(e.message, "danger"),
  });
}

export function useHandoverBatch() {
  const invalidate = useInvalidateStation();
  const toast = useUiStore((s) => s.toast);
  return useMutation({
    mutationFn: (codes: string[]) => stationService.handoverBatch(codes),
    onSuccess: (r) => { invalidate(); toast(r.message); },
    onError: (e: ApiError) => toast(e.message, "danger"),
  });
}

export function useWarehouseIn() {
  const invalidate = useInvalidateStation();
  const toast = useUiStore((s) => s.toast);
  return useMutation({
    mutationFn: (v: { code: string }) => stationService.warehouseIn(v.code),
    onSuccess: (r, v) => {
      invalidate(v.code);
      toast(r.message, r.outcome === WI_OUTCOME.COMPLETED ? "ok" : "warn");
    },
    onError: (e: ApiError) => toast(e.message, "danger"),
  });
}
