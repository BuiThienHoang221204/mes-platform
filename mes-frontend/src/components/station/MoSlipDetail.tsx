"use client";

import { forwardRef, useImperativeHandle, useRef } from "react";
import { QRCodeSVG } from "qrcode.react";

import { Printer } from "@/components/common/PhosphorIcons";
import { AppButton } from "@/components/ui/AppButton";
import type { AtStationRow } from "@/types/board";

type Props = { row: AtStationRow };

function MoSlipDetailInner({ row: r }: Props, ref: React.Ref<HTMLDivElement>) {
  const innerRef = useRef<HTMLDivElement>(null);
  useImperativeHandle(ref, () => innerRef.current!, []);

  const qty = Math.round((r.required_sec ?? 0) / 60);
  const packing = r.pcs_per_box > 0 ? `${r.pcs_per_box} pcs/thùng` : "Không đóng thùng";
  const returns =
    r.round_no > 1
      ? `${r.round_no - 1}${r.qc_result ? ` · QC ${r.qc_result}` : ""}`
      : "0";

  const handlePrint = () => {
    const svg = innerRef.current?.querySelector("svg")?.outerHTML ?? "";
    const w = window.open("", "_blank");
    if (!w) return;
    w.document.write(`<!DOCTYPE html>
<html><head><title>Phiếu ${r.code}</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: monospace; padding: 24px; }
  .card { display: flex; gap: 24px; border: 1px solid #ddd; border-radius: 8px; padding: 20px; max-width: 600px; }
  .qr { flex-shrink: 0; display: flex; align-items: flex-start; }
  .info { flex: 1; }
  .code { font-size: 20px; font-weight: bold; margin-bottom: 12px; }
  table { width: 100%; font-size: 14px; }
  td { padding: 4px 0; }
  td:first-child { color: #666; }
  td:last-child { text-align: right; font-weight: 500; }
  @media print { body { padding: 0; } .card { border: none; } }
</style></head><body>
<div class="card">
  <div class="qr">${svg}</div>
  <div class="info">
    <div class="code">${r.code}</div>
    <table>
      <tr><td>Tên con hàng</td><td>${r.product_name}</td></tr>
      <tr><td>Số lượng</td><td>${r.quantity.toLocaleString("vi-VN")} pcs</td></tr>
      <tr><td>TG yêu cầu Step4</td><td>${qty} phút</td></tr>
      <tr><td>Quy cách</td><td>${packing}</td></tr>
      <tr><td>SL còn thiếu</td><td>${r.target_qty.toLocaleString("vi-VN")}</td></tr>
      <tr><td>Số lần trả lại</td><td>${returns}</td></tr>
    </table>
  </div>
</div>
<script>window.onload=()=>{window.print();}</script>
</body></html>`);
    w.document.close();
  };

  return (
    <div ref={innerRef} className="flex flex-col items-center gap-3 border-t border-line px-4 py-5 sm:flex-row sm:items-start sm:gap-4 sm:px-5">
      <QRCodeSVG value={r.code} size={120} level="M" className="shrink-0 sm:h-full sm:w-auto" />
      <div className="flex w-full flex-col gap-1 text-body-sm">
        <span className="font-mono text-title-lg text-center sm:text-left">{r.code}</span>
        <div className="flex flex-col gap-1 sm:grid sm:grid-cols-2 sm:gap-x-4 sm:gap-y-1">
          <div className="flex justify-between"><span className="text-fg-muted">Tên con hàng</span><span className="font-medium">{r.product_name}</span></div>
          <div className="flex justify-between"><span className="text-fg-muted">Số lượng</span><span className="font-medium">{r.quantity.toLocaleString("vi-VN")} pcs</span></div>
          <div className="flex justify-between"><span className="text-fg-muted">TG yêu cầu Step4</span><span className="font-medium">{qty} phút</span></div>
          <div className="flex justify-between"><span className="text-fg-muted">Quy cách</span><span className="font-medium">{packing}</span></div>
          <div className="flex justify-between"><span className="text-fg-muted">SL còn thiếu</span><span className="font-medium">{r.target_qty.toLocaleString("vi-VN")}</span></div>
          <div className="flex justify-between"><span className="text-fg-muted">Số lần trả lại</span><span className="font-medium">{returns}</span></div>
        </div>
        <AppButton
          size="sm"
          className="mt-2 w-full sm:w-auto"
          onClick={handlePrint}
          icon={<Printer size={20} />}
        >
          In bằng trình duyệt
        </AppButton>
      </div>
    </div>
  );
}

export const MoSlipDetail = forwardRef<HTMLDivElement, Props>(MoSlipDetailInner);
