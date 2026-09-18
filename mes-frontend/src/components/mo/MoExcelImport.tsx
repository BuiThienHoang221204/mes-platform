"use client";

import { useRef, useState } from "react";

import { UploadSimple, WarningCircle } from "@/components/common/PhosphorIcons";
import { AppButton } from "@/components/ui/AppButton";
import { DataTable, type Column } from "@/components/ui/DataTable";
import { Note } from "@/components/ui/Note";
import { useMoActions } from "@/hooks/mo/useMo";
import { EXCEL_COLUMNS, parseExcel, type ParsedRow } from "@/utils/excelImport";
import { dur, nfmt } from "@/utils/format";

const PREVIEW = 50;

const COLUMNS: Column[] = [
  { label: "Dòng", right: true, cellClassName: "text-fg-subtle" },
  { label: "Mã lệnh", cellClassName: "font-mono" },
  { label: "Con hàng" },
  { label: "Số lượng", right: true },
  { label: "TG yêu cầu", right: true },
  { label: "Quy cách", right: true },
  { label: "" },
];

export function MoExcelImport() {
  const { importExcel } = useMoActions();
  const input = useRef<HTMLInputElement>(null);
  const [fileName, setFileName] = useState<string | null>(null);
  const [rows, setRows] = useState<ParsedRow[]>([]);
  const [fileError, setFileError] = useState<string | null>(null);
  const [reading, setReading] = useState(false);

  const bad = rows.filter((r) => r.errors.length);
  const good = rows.filter((r) => !r.errors.length);

  const reset = () => {
    setFileName(null);
    setRows([]);
    setFileError(null);
    if (input.current) input.current.value = "";
  };

  const pick = async (file: File | undefined) => {
    if (!file) return;
    setReading(true);
    setFileName(file.name);
    const res = await parseExcel(file);
    setRows(res.rows);
    setFileError(res.fileError);
    setReading(false);
  };

  const body = rows.slice(0, PREVIEW).map((r) => ({
    key: String(r.line),
    className: r.errors.length ? "bg-danger-soft" : "",
    cells: [
      r.line,
      r.item.code || "—",
      r.item.product_name || "—",
      r.item.quantity ? nfmt(r.item.quantity) : "—",
      r.item.required_production_sec ? dur(r.item.required_production_sec) : "—",
      r.item.pcs_per_box ? nfmt(r.item.pcs_per_box) : "không đóng thùng",
      r.errors.length ? (
        <span className="flex items-center gap-1.5 text-body-sm text-danger">
          <WarningCircle size={18} aria-hidden />
          {r.errors.join(" · ")}
        </span>
      ) : null,
    ],
  }));

  return (
    <div className="space-y-4">
      <input
        ref={input}
        id="excel"
        type="file"
        accept=".xlsx,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        onChange={(e) => pick(e.target.files?.[0])}
        className="sr-only"
      />

      <label
        htmlFor="excel"
        className="flex min-h-32 cursor-pointer flex-col items-center justify-center gap-2 rounded-card border-2 border-dashed border-line-strong bg-surface-2 px-5 py-6 text-center hover:border-accent"
      >
        <UploadSimple size={28} aria-hidden className="text-fg-subtle" />
        <span className="text-body text-fg">
          {fileName ?? "Chọn tệp .xlsx từ máy"}
        </span>
        <span className="text-body-sm text-fg-muted">
          Dòng tiêu đề có hay không đều được. Cột thứ sáu trở đi bỏ qua.
        </span>
      </label>

      <ul className="grid gap-x-6 gap-y-1 text-body-sm text-fg-muted sm:grid-cols-2">
        {EXCEL_COLUMNS.map((c) => (
          <li key={c.at} className="flex gap-2">
            <span className="w-4 shrink-0 font-mono text-fg-subtle">{c.at}</span>
            <span className="text-fg">{c.label}</span>
            {c.note ? <span className="min-w-0 truncate">{c.note}</span> : null}
          </li>
        ))}
      </ul>

      {reading ? <p className="text-body text-fg-subtle">Đang đọc tệp…</p> : null}

    {fileError ? <Note tone="danger">{fileError}</Note> : null}

      {bad.length ? (
        <Note tone="danger">
          <strong>{bad.length} dòng sai — chưa nhập được dòng nào.</strong> Sửa trong tệp Excel
          rồi chọn lại. Nhập một nửa rồi báo lỗi sau thì phải dò xem lệnh nào đã vào, lệnh nào
          chưa.
        </Note>
      ) : null}

      {rows.length ? (
        <>
          <DataTable columns={COLUMNS} rows={body} pad="sm" maxHeight="26rem" />
          {rows.length > PREVIEW ? (
            <p className="text-body-sm text-fg-subtle">
              Đang xem {PREVIEW} dòng đầu trên tổng {nfmt(rows.length)} dòng. Nút dưới nhập trọn
              tệp.
            </p>
          ) : null}
        </>
      ) : null}

      <div className="flex flex-wrap gap-2">
        <AppButton
          variant="primary"
          disabled={!good.length || bad.length > 0 || importExcel.isPending}
          onClick={() => importExcel.mutate(good.map((r) => r.item), { onSuccess: reset })}
        >
          Nhập {rows.length ? nfmt(good.length) : ""} lệnh
        </AppButton>
        {rows.length || fileError ? (
          <AppButton onClick={reset}>Chọn tệp khác</AppButton>
        ) : null}
      </div>
    </div>
  );
}
