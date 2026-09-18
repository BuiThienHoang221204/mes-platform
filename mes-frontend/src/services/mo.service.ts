import { deleteData, getData, postData } from "./http";
import { PAGE_SIZE } from "@/constants/pagination";
import type { OkOut, Page } from "@/types/api";
import type { MoOut, MoStatus } from "@/types/mo";

export type MoListQuery = { status?: MoStatus; dateFrom?: string; dateTo?: string };

export type MoCreatePayload = {
  code: string; product_name: string; quantity: number;
  required_production_min: number; pcs_per_box: number;
};

export type MoExcelRow = {
  code: string;
  product_name: string;
  quantity: number;
  required_production_sec: number;
  pcs_per_box: number;
};

export type LineRow = { id: number; code: string; name: string | null; is_active: boolean };

export const moService = {
  list: (q: MoListQuery = {}, limit = PAGE_SIZE, offset = 0) =>
    getData<Page<MoOut>>("/mos", {
      ...(q.status ? { status: q.status } : {}),
      ...(q.dateFrom ? { date_from: q.dateFrom } : {}),
      ...(q.dateTo ? { date_to: q.dateTo } : {}),
      limit,
      offset,
    }),
  detail: (code: string) => getData<MoOut>(`/mos/${code}`),
  create: (p: MoCreatePayload) => postData<MoOut[]>("/mos", p),
  importExcel: (rows: MoExcelRow[]) =>
    postData<MoOut[], { items: MoExcelRow[] }>("/mos/import-excel", { items: rows }),
  submit: (code: string) => postData<OkOut>(`/mos/${code}/submit`),
  submitBatch: (codes: string[]) =>
    postData<OkOut, { codes: string[] }>("/mos/submit-batch", { codes }),
  cancelBatch: (codes: string[], reason: string) =>
    postData<OkOut, { codes: string[]; reason: string }>("/mos/cancel-batch", {
      codes,
      reason,
    }),
  cancel: (code: string, reason: string) => postData<OkOut>(`/mos/${code}/cancel`, { reason }),
};

export const catalogService = {
  lines: () => getData<LineRow[]>("/lines"),
  createLine: (code: string, name: string) => postData<LineRow>("/lines", { code, name }),
  deleteLine: (code: string) => deleteData<OkOut>(`/lines/${code}`),
};
