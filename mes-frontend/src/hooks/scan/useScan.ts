"use client";

import { useMutation } from "@tanstack/react-query";
import { stationService } from "@/services/station.service";
import { useInvalidateStation } from "@/hooks/useInvalidateStation";
import { useScanStore } from "@/stores/useScanStore";
import { useStationStore } from "@/stores/useStationStore";
import { useUiStore } from "@/stores/useUiStore";
import type { ApiError } from "@/types/api";

/**
 * R6 — `/scan` là POST và TẠO bản ghi, nên là mutation dù "cảm giác" như đọc.
 * Trạm lấy từ token của THIẾT BỊ, không phải từ body.
 */
export function useScan() {
  const token = useStationStore((s) => s.stationToken);
  const setResult = useScanStore((s) => s.setResult);
  const setError = useScanStore((s) => s.setError);
  const toast = useUiStore((s) => s.toast);
  const invalidate = useInvalidateStation();

  return useMutation({
    mutationFn: (raw: string) => {
      if (!token) throw { code: "NO_STATION", message: "Thiết bị chưa đăng ký trạm.", status: 0 } as ApiError;
      return stationService.scan(raw, token);
    },
    onSuccess: (r) => {
      setResult(r);
      invalidate(r.mo_code);
      toast(r.duplicate ? `${r.mo_code} — đã nhận rồi` : r.message, r.duplicate ? "warn" : "ok");
    },
    onError: (e: ApiError) => { setError(e.message); toast(e.message, "danger"); },
  });
}
