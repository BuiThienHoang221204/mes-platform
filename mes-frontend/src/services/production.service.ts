import { getData, postData } from "./http";
import type { OkOut } from "@/types/api";
import type { PackingHourlyOut } from "@/types/mo";
import type { Trace } from "@/types/trace";

export type HourlyPayload = {
  work_date: string; slot_hour: number;
  headcount: number; target_qty: number; qty: number; note?: string | null;
};

export type ClosePayload = {
  qty_ok: number; qty_ng: number; qty_short: number;
  ng_reason_text?: string | null; short_reason_text?: string | null;
};

export const productionService = {
  trace: (code: string) => getData<Trace>(`/mos/${code}/trace`),
  lines: () => getData<{ id: number; code: string; name: string | null; is_active: boolean }[]>("/lines"),

  assign: (code: string, line_code: string) => postData<OkOut>(`/lines/${code}/assign`, { line_code }),
  start: (code: string, line_code: string) => postData<OkOut>(`/lines/${code}/start`, { line_code }),
  hold: (code: string, line_code: string, reason_text: string) =>
    postData<OkOut>(`/lines/${code}/hold`, { line_code, reason_code_id: null, reason_text }),

  close: (code: string, p: ClosePayload) =>
    postData<OkOut>(`/production/${code}/close`, {
      ...p, ng_reason_code_id: null, short_reason_code_id: null,
    }),

  hourly: (code: string, p: HourlyPayload) => postData<OkOut>(`/hourly/${code}`, p),

  packStart: (code: string) => postData<OkOut>(`/packing/${code}/start`),
  packHourly: (code: string, p: { work_date: string; slot_hour: number; boxes: number; note?: string | null }) =>
    postData<PackingHourlyOut>(`/packing/${code}/hourly`, p),
  packFinish: (code: string, qty_packed: number, note_text: string) =>
    postData<OkOut>(`/packing/${code}/finish`, { qty_packed, note_text }),
};
