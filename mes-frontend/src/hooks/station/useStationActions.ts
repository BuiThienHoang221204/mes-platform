"use client";

import { useMutation } from "@tanstack/react-query";
import { stationService } from "@/services/station.service";
import { useInvalidateStation } from "@/hooks/useInvalidateStation";
import { useUiStore } from "@/stores/useUiStore";
import type { ApiError } from "@/types/api";
import { QC_RESULT, WI_OUTCOME, type QcResultValue } from "@/constants/status";

/** Ba thao tác trạm đã nối API. Trạm 1 và 3 KHÔNG có ở đây — chúng không có việc gì để làm. */
export function useHandover() {
  const invalidate = useInvalidateStation();
  const toast = useUiStore((s) => s.toast);
  return useMutation({
    mutationFn: (code: string) => stationService.handover(code),
    onSuccess: (r, code) => { invalidate(code); toast(r.message); },
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

export function useQcDecide() {
  const invalidate = useInvalidateStation();
  const toast = useUiStore((s) => s.toast);
  return useMutation({
    mutationFn: (v: {
      code: string;
      result: QcResultValue;
      reasonCodeId?: number | null;
      reasonText?: string | null;
    }) => stationService.qc(v.code, v.result, { codeId: v.reasonCodeId, text: v.reasonText }),
    onSuccess: (r, v) => { invalidate(v.code); toast(r.message, r.result === QC_RESULT.PASS ? "ok" : "warn"); },
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
