"use client";

import { useEffect, useState } from "react";

import { Truck } from "@/components/common/PhosphorIcons";
import { AppButton } from "@/components/ui/AppButton";
import { AppModal } from "@/components/ui/AppModal";
import { useHandover } from "@/hooks/station/useStationActions";
import type { AtStationRow } from "@/types/board";
import { nfmt } from "@/utils/format";

type Props = {
  row: AtStationRow | null;
  onClose: () => void;
};

export function HandoverModal({ row, onClose }: Props) {
  const handover = useHandover();
  const [note, setNote] = useState("");

  useEffect(() => {
    if (row) {
      setNote("");
    }
  }, [row]);

  const handleClose = () => {
    setNote("");
    onClose();
  };

  const handleConfirm = () => {
    if (!row) return;
    handover.mutate(
      { code: row.code, note: note.trim() || undefined },
      { onSuccess: handleClose }
    );
  };

  return (
    <AppModal
      open={Boolean(row)}
      title={`Bàn giao xuống Setup · ${row?.code ?? ""}`}
      onClose={handleClose}
      footer={
        <>
          <AppButton variant="ghost" onClick={handleClose}>
            Huỷ
          </AppButton>
          <AppButton
            variant="primary"
            disabled={handover.isPending}
            onClick={handleConfirm}
            icon={<Truck size={24} />}
          >
            {handover.isPending ? "Đang bàn giao…" : "Xác nhận bàn giao"}
          </AppButton>
        </>
      }
    >
      <div className="space-y-4">
        <div className="rounded-card border border-line bg-surface-2 px-4 py-3 sm:px-5">
          <p className="text-caption font-medium text-fg-muted">THÔNG TIN LỆNH</p>
          <div className="mt-2 grid grid-cols-2 gap-x-4 gap-y-2 text-body-sm">
            <div>
              <span className="text-fg-muted">Con hàng:</span>{" "}
              <span className="font-medium text-fg">{row?.product_name}</span>
            </div>
            <div>
              <span className="text-fg-muted">Số lượng:</span>{" "}
              <span className="font-medium text-fg">
                {nfmt(row?.target_qty ?? row?.quantity ?? 0)} pcs
              </span>
            </div>
            <div>
              <span className="text-fg-muted">Vòng:</span>{" "}
              <span className="font-medium text-fg">Vòng {row?.round_no}</span>
            </div>
            <div>
              <span className="text-fg-muted">Nhận lúc:</span>{" "}
              <span className="font-medium text-fg">
                {row?.accepted_at ? row.accepted_at.slice(11, 16) : "—"}
              </span>
            </div>
          </div>
        </div>

        <div className="space-y-1.5">
          <label htmlFor="handover-note" className="block text-label text-fg-muted">
            Ghi chú cho thợ Setup máy (không bắt buộc)
          </label>
          <textarea
            id="handover-note"
            rows={3}
            value={note}
            onChange={(e) => setNote(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
                e.preventDefault();
                handleConfirm();
              }
            }}
            placeholder="Ví dụ: Giao trước 200 phôi làm thử, khuôn cần canh kỹ chốt định vị..."
            className="w-full rounded-field border border-line-strong bg-surface px-4 py-2.5 text-body text-fg placeholder:text-fg-subtle focus:border-accent focus:outline-none"
            maxLength={500}
          />
          <p className="text-caption text-fg-subtle">
            Thợ Setup máy sẽ nhìn thấy ghi chú này ngay tại Hàng đợi trước khi quét nhận (nhấn Ctrl+Enter để xác nhận nhanh).
          </p>
        </div>
      </div>
    </AppModal>
  );
}
