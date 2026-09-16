"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import { catalogKeys, moKeys } from "@/constants/queryKeys";
import { productionService, type ClosePayload, type HourlyPayload } from "@/services/production.service";
import { useInvalidateStation } from "@/hooks/useInvalidateStation";
import { useUiStore } from "@/stores/useUiStore";
import type { ApiError } from "@/types/api";

export const useTrace = (code: string | null) =>
  useQuery({
    queryKey: moKeys.trace(code ?? ""),
    queryFn: () => productionService.trace(code as string),
    enabled: !!code,
    staleTime: 5_000,
  });

/** Danh mục gần như không đổi — `staleTime: Infinity` (R4). */
export const useLines = () =>
  useQuery({ queryKey: catalogKeys.lines(), queryFn: productionService.lines, staleTime: Infinity });

/**
 * Tám mutation của trạm 4 dùng CHUNG một cách báo lỗi và một cách làm mới dữ liệu.
 *
 * Phần dùng chung nằm ở `sharedOptions` — một hàm THƯỜNG trả về object options,
 * KHÔNG phải hàm gọi `useMutation` hộ. Gọi hook bên trong helper là vi phạm
 * rules-of-hooks: nó chạy đúng hôm nay, nhưng thêm một nhánh `if` là vỡ.
 */
function useShared(code: string | null) {
  const invalidate = useInvalidateStation();
  const toast = useUiStore((s) => s.toast);

  // KHÔNG gắn generic cho options: ghim `TVariables` ở đây là nó lây sang mọi
  // mutation và biến tham số của chúng thành `never`.
  return () => ({
    onSuccess: (r: unknown) => {
      invalidate(code ?? undefined);
      const msg = (r as { message?: string })?.message;
      if (msg) toast(msg);
    },
    // `http.ts` bảo đảm mọi lỗi ném ra đã là `ApiError`.
    onError: (e: unknown) => toast((e as ApiError).message, "danger"),
  });
}

export function useProductionActions(code: string | null) {
  const shared = useShared(code);
  const mo = code as string;

  const assign = useMutation({
    mutationFn: (line: string) => productionService.assign(mo, line),
    ...shared(),
  });
  const start = useMutation({
    mutationFn: (line: string) => productionService.start(mo, line),
    ...shared(),
  });
  const hold = useMutation({
    mutationFn: (v: { line: string; reason: string }) => productionService.hold(mo, v.line, v.reason),
    ...shared(),
  });
  const close = useMutation({
    mutationFn: (p: ClosePayload) => productionService.close(mo, p),
    ...shared(),
  });
  const hourly = useMutation({
    mutationFn: (p: HourlyPayload) => productionService.hourly(mo, p),
    ...shared(),
  });
  const packStart = useMutation({
    mutationFn: () => productionService.packStart(mo),
    ...shared(),
  });
  const packHourly = useMutation({
    mutationFn: (p: { work_date: string; slot_hour: number; boxes: number }) =>
      productionService.packHourly(mo, p),
    ...shared(),
  });
  const packFinish = useMutation({
    mutationFn: (v: { qty: number; note: string }) => productionService.packFinish(mo, v.qty, v.note),
    ...shared(),
  });

  return { assign, start, hold, close, hourly, packStart, packHourly, packFinish };
}
