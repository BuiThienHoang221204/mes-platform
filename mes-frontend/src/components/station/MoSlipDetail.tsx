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
    <div ref={innerRef} className="flex gap-4 border-t border-line px-4 py-5 sm:px-5">
      <QRCodeSVG value={r.code} size={160} level="M" className="h-full shrink-0" />
      <div className="flex flex-1 flex-col gap-1 text-body-sm">
        <span className="font-mono text-title-lg">{r.code}</span>
        <div className="grid grid-cols-2 gap-x-4 gap-y-1">
          <span className="text-fg-muted">Tên con hàng</span>
          <span className="text-right font-medium">{r.product_name}</span>
          <span className="text-fg-muted">Số lượng</span>
          <span className="text-right font-medium">
            {r.quantity.toLocaleString("vi-VN")} pcs
          </span>
          <span className="text-fg-muted">TG yêu cầu Step4</span>
          <span className="text-right font-medium">{qty} phút</span>
          <span className="text-fg-muted">Quy cách</span>
          <span className="text-right font-medium">{packing}</span>
          <span className="text-fg-muted">SL còn thiếu</span>
          <span className="text-right font-medium">
            {r.target_qty.toLocaleString("vi-VN")}
          </span>
          <span className="text-fg-muted">Số lần trả lại</span>
          <span className="text-right font-medium">{returns}</span>
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
