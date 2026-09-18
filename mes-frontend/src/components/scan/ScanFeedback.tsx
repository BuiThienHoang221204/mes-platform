"use client";

import { CheckCircle, QrCode, XCircle } from "@/components/common/PhosphorIcons";
import { useScanStore } from "@/stores/useScanStore";

/**
 * Phản hồi của lần quét vừa rồi, CHỈ cho trạm đang mở.
 *
 * Kết quả của trạm khác coi như chưa quét gì ở đây — quét ở Kho xuất rồi bấm sang
 * Setup mà vẫn thấy "Kho xuất đã nhận" thì người đứng máy hiểu là Setup vừa nhận.
 */
export function ScanFeedback({ station }: { station: number }) {
  const mine = useScanStore((s) => s.station === station);
  const last = useScanStore((s) => s.last);
  const lastError = useScanStore((s) => s.lastError);

  if (mine && lastError) {
    return (
      <div className="flex items-start gap-3 rounded-field bg-danger-soft px-4 py-3 text-body-sm text-danger">
        <XCircle size={22} weight="fill" className="shrink-0" />
        <span>{lastError}</span>
      </div>
    );
  }

  if (mine && last) {
    const tone = last.duplicate ? "bg-warn-soft text-warn" : "bg-ok-soft text-ok";
    return (
      <div className={`flex items-start gap-3 rounded-field px-4 py-3 text-body-sm ${tone}`}>
        <CheckCircle size={22} weight="fill" className="shrink-0" />
        <span>
          <span className="font-mono">{last.mo_code}</span> · vòng {last.round_no} — {last.message}
        </span>
      </div>
    );
  }

  return (
    <div className="flex items-start gap-3 rounded-field bg-surface-2 px-4 py-3 text-body-sm text-fg-muted">
      <QrCode size={22} className="shrink-0" />
      <span>Đưa mã QR vào đầu đọc, hoặc bấm một dòng trong hàng đợi để nạp mã.</span>
    </div>
  );
}
