"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { PAGE_SIZE } from "@/constants/pagination";
import { boardKeys, catalogKeys, moKeys } from "@/constants/queryKeys";
import {
  catalogService,
  moService,
  type MoExcelRow,
  type MoCreatePayload,
  type MoListQuery,
} from "@/services/mo.service";
import { useUiStore } from "@/stores/useUiStore";
import type { ApiError } from "@/types/api";

/** Một TRANG sổ lệnh. `total` để biết còn trang sau không — trước đây repository có
 *  `limit=200` viết cứng, tới lệnh thứ 201 là màn hình mất lệnh mà không báo gì. */
export const useMoList = (loc: MoListQuery = {}, offset = 0, limit = PAGE_SIZE) => {
  const q = useQuery({
    queryKey: [
      ...moKeys.all, "list",
      loc.status ?? "all", loc.dateFrom ?? "", loc.dateTo ?? "",
      limit, offset,
    ],
    queryFn: () => moService.list(loc, limit, offset),
    staleTime: 10_000,
  });
  return { ...q, items: q.data?.items ?? [], total: q.data?.total ?? 0, limit, offset };
};

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
  const importExcel = useMutation({
    mutationFn: (rows: MoExcelRow[]) => moService.importExcel(rows),
    onSuccess: (r) => ok(`Đã nhập ${r.length} lệnh từ tệp Excel`),
    onError: err,
  });
  const submitBatch = useMutation({
    mutationFn: (codes: string[]) => moService.submitBatch(codes),
    onSuccess: (r) => ok(r.message),
    onError: err,
  });
  const cancelBatch = useMutation({
    mutationFn: (v: { codes: string[]; reason: string }) =>
      moService.cancelBatch(v.codes, v.reason),
    onSuccess: (r) => ok(r.message),
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

  return { create, importExcel, submit, submitBatch, cancel, cancelBatch };
}

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
