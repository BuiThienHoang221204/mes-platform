import { deleteData, getData, postData } from "./http";
import type { OkOut } from "@/types/api";
import type { MoOut, MoStatus } from "@/types/mo";

export type MoCreatePayload = {
  code: string; product_name: string; quantity: number;
  required_production_min: number; pcs_per_box: number;
};

export type LineRow = { id: number; code: string; name: string | null; is_active: boolean };

export const moService = {
  list: (status?: MoStatus) => getData<MoOut[]>("/mos", status ? { status } : undefined),
  detail: (code: string) => getData<MoOut>(`/mos/${code}`),
  create: (p: MoCreatePayload) => postData<MoOut[]>("/mos", p),
  /** 4 cột bắt buộc + cột 5 QUY CÁCH tuỳ chọn — file CSV cũ của xưởng vẫn nhập được. */
  importCsv: (csv: string) => postData<MoOut[]>("/mos/import", { csv }),
  submit: (code: string) => postData<OkOut>(`/mos/${code}/submit`),
  cancel: (code: string, reason: string) => postData<OkOut>(`/mos/${code}/cancel`, { reason }),
};

export const catalogService = {
  lines: () => getData<LineRow[]>("/lines"),
  createLine: (code: string, name: string) => postData<LineRow>("/lines", { code, name }),
  deleteLine: (code: string) => deleteData<OkOut>(`/lines/${code}`),
};
