"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { boardKeys, catalogKeys, moKeys } from "@/constants/queryKeys";
import { catalogService, moService, type MoCreatePayload } from "@/services/mo.service";
import { useUiStore } from "@/stores/useUiStore";
import type { ApiError } from "@/types/api";
import type { MoStatus } from "@/types/mo";

export const useMoList = (status?: MoStatus) =>
  useQuery({
    queryKey: [...moKeys.all, "list", status ?? "all"],
    queryFn: () => moService.list(status),
    staleTime: 10_000,
  });

export const useTraceMo = (code: string | null) =>
  useQuery({
    queryKey: moKeys.trace(code ?? ""),
    queryFn: () => import("@/services/production.service").then((m) => m.productionService.trace(code as string)),
    enabled: !!code,
    staleTime: 10_000,
  });

/** R3 — tạo/chốt/huỷ lệnh đổi cả hàng đợi lẫn danh sách. */
function useMoInvalidate() {
  const qc = useQueryClient();
  return () => {
    qc.invalidateQueries({ queryKey: moKeys.all });
    qc.invalidateQueries({ queryKey: boardKeys.all });
  };
}

export function useMoActions() {
  const invalidate = useMoInvalidate();
  const toast = useUiStore((s) => s.toast);
  const ok = (msg: string) => { invalidate(); toast(msg); };
  const err = (e: unknown) => toast((e as ApiError).message, "danger");

  const create = useMutation({
    mutationFn: (p: MoCreatePayload) => moService.create(p),
    onSuccess: (r) => ok(`Đã tạo ${r[0]?.code ?? "lệnh"} — trạng thái Nháp`),
    onError: err,
  });
  const importCsv = useMutation({
    mutationFn: (csv: string) => moService.importCsv(csv),
    onSuccess: (r) => ok(`Đã nhập ${r.length} lệnh từ CSV`),
    onError: err,
  });
  const submit = useMutation({
    mutationFn: (code: string) => moService.submit(code),
    onSuccess: (r) => ok(r.message),
    onError: err,
  });
  const cancel = useMutation({
    mutationFn: (v: { code: string; reason: string }) => moService.cancel(v.code, v.reason),
    onSuccess: (r) => ok(r.message),
    onError: err,
  });

  return { create, importCsv, submit, cancel };
}

export const useCatalogLines = () =>
  useQuery({ queryKey: catalogKeys.lines(), queryFn: catalogService.lines, staleTime: Infinity });

export function useLineActions() {
  const qc = useQueryClient();
  const toast = useUiStore((s) => s.toast);
  const done = () => qc.invalidateQueries({ queryKey: catalogKeys.lines() });
  const err = (e: unknown) => toast((e as ApiError).message, "danger");

  const create = useMutation({
    mutationFn: (v: { code: string; name: string }) => catalogService.createLine(v.code, v.name),
    onSuccess: (r) => { done(); toast(`Đã thêm chuyền ${r.code}`); },
    onError: err,
  });
  /** Chuyền đã chạy MO thì khoá ngoại chặn — câu lỗi tiếng Việt gợi ý TẮT thay vì xoá. */
  const remove = useMutation({
    mutationFn: (code: string) => catalogService.deleteLine(code),
    onSuccess: (r) => { done(); toast(r.message); },
    onError: err,
  });

  return { create, remove };
}
