"use client";

import { AppButton } from "@/components/ui/AppButton";
import { AppModal } from "@/components/ui/AppModal";
import { Note } from "@/components/ui/Note";
import { QtyStat } from "@/components/ui/QtyStat";
import { useWarehouseIn } from "@/hooks/station/useStationActions";
import type { AtStationRow } from "@/types/board";
import { boxLabel, boxesOf, nfmt } from "@/utils/format";

type Props = {
  row: AtStationRow | null;
  onClose: () => void;
};

/**
 * Kho nhập XÁC NHẬN, không khai lại số.
 *
 * Trước đây màn này có ô `Đếm lại được bao nhiêu`. Con số ấy được ghi xuống CSDL
 * nhưng không ai đọc — §8 tính tiến độ từ `SL đã đóng thùng`, nên gõ 0 hay 999.999
 * đều ra cùng một kết cục. Một ô nhập không đổi được gì còn tệ hơn ô nhập sai.
 *
 * Hàng đã vào thùng bao nhiêu thì kho nhận bấy nhiêu. Thùng thất lạc dọc đường là
 * sự cố kho, không phải sản xuất thiếu — bắt xưởng chạy thêm một vòng để bù cho
 * một thùng bị mất là bắt sai người.
 *
 * Số dẫn là SỐ THÙNG, pcs xuống dòng phụ: kho đếm thùng, không đếm hàng rời (§7b.2).
 * Nhưng mọi phép tính vẫn chạy bằng pcs — đưa đơn vị thô vào giữa dây số học là chỗ
 * sinh lỗi, vì đơn hàng hiếm khi chia hết cho quy cách.
 */
export function CompleteModal({ row, onClose }: Props) {
  const complete = useWarehouseIn();

  const packed = row?.qty_packed ?? 0;
  const perBox = row?.pcs_per_box ?? 0;
  const boxes = boxesOf(packed, perBox);

  const run = () => {
    if (!row) return;
    complete.mutate({ code: row.code }, { onSuccess: onClose });
  };

  return (
    <AppModal
      open={Boolean(row)}
      title={`Nhập kho · ${row?.code ?? ""}`}
      onClose={onClose}
      footer={
        <>
          <AppButton variant="ghost" onClick={onClose}>
            Huỷ
          </AppButton>
          <AppButton variant="primary" disabled={complete.isPending} onClick={run}>
            Xác nhận đã nhận
          </AppButton>
        </>
      }
    >
      <div className="space-y-5">
        <div className="rounded-card border border-accent-line bg-accent-soft px-4 py-4 sm:px-5">
          <p className="text-caption text-accent">Nhận về kho</p>
          <p className="mt-1 text-h1 tnum text-accent sm:text-display">{boxLabel(packed, perBox)}</p>
          <p className="mt-1 text-body-sm text-fg-muted">
            {nfmt(packed)} pcs
            {boxes ? ` · quy cách ${nfmt(perBox)} pcs/thùng` : " · mặt hàng không đóng thùng"}
          </p>
          {boxes?.rest ? (
            <p className="mt-1 text-body-sm text-fg-muted">
              Thùng cuối đóng thiếu: {nfmt(boxes.rest)}/{nfmt(perBox)} pcs — đúng quy định,
              không phải sai sót.
            </p>
          ) : null}
        </div>

        <div className="grid gap-3 sm:grid-cols-2">
          <QtyStat label="SL kế hoạch" value={row?.quantity ?? 0} unit="pcs" />
          <QtyStat label="Mục tiêu vòng" value={row?.target_qty ?? 0} unit="pcs" tone="warn" />
        </div>

        <Note>
          <strong className="text-ok">Đủ số</strong> — lệnh đóng lại, hoàn thành.{" "}
          <strong className="text-warn">Thiếu số</strong> — lệnh tự mở vòng mới và quay về Bàn
          team leader, không qua lại Kho xuất, Setup hay QC.
        </Note>
      </div>
    </AppModal>
  );
}
