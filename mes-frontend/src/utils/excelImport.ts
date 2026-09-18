import { readSheet, type Row } from "read-excel-file/browser";

import { MO_CODE_EXACT } from "@/utils/moCode";
import type { MoExcelRow } from "@/services/mo.service";

export const EXCEL_COLUMNS = [
  { at: "A", label: "Mã lệnh", note: "chữ M kèm đúng 6 chữ số" },
  { at: "B", label: "Tên con hàng", note: "" },
  { at: "C", label: "Số lượng", note: "pcs" },
  { at: "D", label: "Giờ yêu cầu", note: "giờ, chỉ cho bước Sản xuất" },
  { at: "E", label: "Quy cách", note: "pcs/thùng · trống = không đóng thùng" },
] as const;

export const MAX_IMPORT_ROWS = 2000;

export type ParsedRow = {
  line: number;
  item: MoExcelRow;
  errors: string[];
};

export type ParseResult = {
  rows: ParsedRow[];
  fileError: string | null;
};

const text = (v: unknown) => (v == null ? "" : String(v).trim());

const num = (v: unknown): number | null => {
  if (typeof v === "number") return Number.isFinite(v) ? v : null;
  const s = text(v).replace(/\s/g, "").replace(",", ".");
  if (!s) return null;
  const n = Number(s);
  return Number.isFinite(n) ? n : null;
};

const hoursToSeconds = (hours: number) => Math.max(1, Math.round(hours * 3600));

const looksLikeData = (row: Row | undefined) =>
  row != null && MO_CODE_EXACT.test(text(row[0]).toUpperCase());

function readRow(raw: Row, line: number): ParsedRow {
  const errors: string[] = [];

  const code = text(raw[0]).toUpperCase();
  if (!MO_CODE_EXACT.test(code)) errors.push("Mã phải là chữ M kèm đúng 6 chữ số");

  const name = text(raw[1]);
  if (!name) errors.push("Thiếu tên con hàng");

  const qty = num(raw[2]);
  if (qty == null || !Number.isInteger(qty) || qty <= 0) errors.push("Số lượng phải là số nguyên > 0");

  const hours = num(raw[3]);
  if (hours == null || hours <= 0) errors.push("Giờ yêu cầu phải là số > 0");

  const box = raw[4] == null || text(raw[4]) === "" ? 0 : num(raw[4]);
  if (box == null || !Number.isInteger(box) || box < 0) errors.push("Quy cách phải là số nguyên ≥ 0");

  return {
    line,
    errors,
    item: {
      code,
      product_name: name,
      quantity: qty ?? 0,
      required_production_sec: hours == null ? 0 : hoursToSeconds(hours),
      pcs_per_box: box ?? 0,
    },
  };
}

function markDuplicates(rows: ParsedRow[]) {
  const seen = new Map<string, number>();
  for (const r of rows) {
    if (!r.item.code) continue;
    const first = seen.get(r.item.code);
    if (first == null) seen.set(r.item.code, r.line);
    else r.errors.push(`Mã trùng với dòng ${first} trong cùng tệp`);
  }
}

export async function parseExcel(file: File): Promise<ParseResult> {
  let raw: Row[];
  try {
    raw = await readSheet(file);
  } catch {
    return { rows: [], fileError: "Không đọc được tệp — cần đúng định dạng .xlsx" };
  }

  const skipHeader = !looksLikeData(raw[0]);
  const body = raw.slice(skipHeader ? 1 : 0).filter((r) => r.some((c) => text(c) !== ""));
  if (!body.length) return { rows: [], fileError: "Tệp không có dòng dữ liệu nào" };
  if (body.length > MAX_IMPORT_ROWS) {
    return {
      rows: [],
      fileError: `Tệp ${body.length} dòng, quá trần ${MAX_IMPORT_ROWS} — cắt nhỏ rồi nhập nhiều lần`,
    };
  }

  const rows = body.map((r, i) => readRow(r, i + (skipHeader ? 2 : 1)));
  markDuplicates(rows);
  return { rows, fileError: null };
}
