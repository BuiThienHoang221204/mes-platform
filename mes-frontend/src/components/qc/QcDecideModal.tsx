"use client";

import { useState } from "react";

import { Warning } from "@/components/common/PhosphorIcons";
import { AppButton } from "@/components/ui/AppButton";
import { AppInput } from "@/components/ui/AppInput";
import { AppModal } from "@/components/ui/AppModal";
import { AppSelect } from "@/components/ui/AppSelect";
import { QC_RESULT } from "@/constants/status";
import { REASON_GROUP } from "@/constants/reasons";
import { useReasons } from "@/hooks/catalog/useReasons";
import { useQcDecide } from "@/hooks/station/useStationActions";

type Props = {
  code: string | null;
  onClose: () => void;
};

export function QcDecideModal({ code, onClose }: Props) {
  const decide = useQcDecide();
  const { data: reasons } = useReasons(REASON_GROUP.QC);
  const [reasonId, setReasonId] = useState("");
  const [note, setNote] = useState("");

  const close = () => {
    setReasonId("");
    setNote("");
    onClose();
  };

  const run = (result: typeof QC_RESULT.PASS | typeof QC_RESULT.FAIL) => {
    if (!code) return;
    decide.mutate(
      {
        code,
        result,
        reasonCodeId: result === QC_RESULT.FAIL ? Number(reasonId) : null,
        reasonText: result === QC_RESULT.FAIL ? note.trim() || null : null,
      },
      { onSuccess: close },
    );
  };

  const options = (reasons ?? []).filter((r) => r.is_active).map((r) => ({ value: r.id, label: r.name }));

  return (
    <AppModal open={Boolean(code)} title={`Kết quả kiểm · ${code ?? ""}`} onClose={close}>
      <div className="space-y-6">
        <AppButton
          variant="primary"
          size="lg"
          block
          disabled={decide.isPending}
          onClick={() => run(QC_RESULT.PASS)}
        >
          Đạt — chuyển Bàn team leader
        </AppButton>

        <div className="space-y-4 rounded-card border border-line p-4">
          <p className="flex items-start gap-2 text-body-sm text-warn">
            <Warning size={20} weight="fill" className="mt-0.5 shrink-0" />
            <span className="min-w-0">
              Không đạt thì lệnh <strong>về Kho xuất</strong> và mở vòng mới — không về Bàn team
              leader, vì setup sai mà bỏ qua Setup và QC là hàng lỗi đi thẳng vào chuyền.
            </span>
          </p>

          <AppSelect
            label="Lý do không đạt"
            options={options}
            value={reasonId}
            placeholder="Chọn lý do"
            onChange={(e) => setReasonId(e.target.value)}
          />

          <AppInput
            label="Ghi thêm"
            placeholder="Mô tả để Setup biết chỉnh gì"
            value={note}
            onChange={(e) => setNote(e.target.value)}
          />

          <AppButton
            variant="danger"
            size="lg"
            block
            disabled={decide.isPending || !reasonId}
            onClick={() => run(QC_RESULT.FAIL)}
          >
            Không đạt — trả về Kho, mở vòng mới
          </AppButton>
        </div>
      </div>
    </AppModal>
  );
}
