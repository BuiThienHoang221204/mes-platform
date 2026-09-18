"use client";

import { useEffect, useState } from "react";

import { AppButton } from "@/components/ui/AppButton";
import { AppInput } from "@/components/ui/AppInput";
import { AppModal } from "@/components/ui/AppModal";
import { AppSelect } from "@/components/ui/AppSelect";
import { REASON_GROUP } from "@/constants/reasons";
import { useReasons } from "@/hooks/catalog/useReasons";

type Props = {
  open: boolean;
  code: string;
  /** Chỉ những chuyền ĐANG chạy mới dừng được. */
  running: string[];
  busy?: boolean;
  onClose: () => void;
  onHold: (lines: string[], reason: string) => void;
};

export function HoldLineModal({ open, code, running, busy, onClose, onHold }: Props) {
  const { data: reasons } = useReasons(REASON_GROUP.HOLD);
  const [picked, setPicked] = useState<string[]>([]);
  const [reason, setReason] = useState("");
  const [note, setNote] = useState("");

  // Một chuyền thì không có gì để chọn — tick sẵn, đỡ một thao tác thừa.
  useEffect(() => {
    if (open) setPicked(running.length === 1 ? [running[0]] : []);
  }, [open, running]);

  const close = () => {
    onClose();
    setPicked([]);
    setReason("");
    setNote("");
  };

  const toggle = (c: string) =>
    setPicked((p) => (p.includes(c) ? p.filter((x) => x !== c) : [...p, c]));

  return (
    <AppModal
      open={open}
      title={`Dừng chuyền · ${code}`}
      onClose={close}
      footer={
        <>
          <AppButton variant="ghost" onClick={close}>
            Huỷ
          </AppButton>
          <AppButton
            variant="danger"
            disabled={!picked.length || !reason || busy}
            onClick={() => {
              onHold(picked, [reason, note.trim()].filter(Boolean).join(" — "));
              close();
            }}
          >
            Dừng {picked.length > 1 ? `${picked.length} chuyền` : "chuyền"}
          </AppButton>
        </>
      }
    >
      <div className="space-y-4">
        <p className="text-body-sm text-fg-muted">
          Thời gian dừng không tính vào thời gian chạy — nó rơi sang cột thời gian chờ, nên KPI
          không bị phạt oan vì máy hỏng.
        </p>

        {running.length > 1 ? (
          <div className="space-y-2">
            <span className="flex items-center gap-3">
              <span className="text-label text-fg-muted">Chuyền nào dừng</span>
              <button
                type="button"
                onClick={() => setPicked(running)}
                className="text-body-sm text-accent underline"
              >
                Chọn tất cả
              </button>
            </span>
            <div className="grid grid-cols-3 gap-2">
              {running.map((c) => (
                <button
                  key={c}
                  type="button"
                  onClick={() => toggle(c)}
                  className={`min-h-touch rounded-field border font-mono text-body-lg ${
                    picked.includes(c)
                      ? "border-danger bg-danger-soft text-danger"
                      : "border-line-strong text-fg"
                  }`}
                >
                  {c}
                </button>
              ))}
            </div>
            <p className="text-caption text-fg-subtle">
              Chỉ tick chuyền thật sự dừng. Tick cả chuyền đang chạy thì đồng hồ của nó đứng oan,
              và KPI sẽ đẹp hơn thực tế.
            </p>
          </div>
        ) : null}

        <AppSelect
          label="Lý do dừng"
          placeholder="Chọn lý do"
          value={reason}
          onChange={(e) => setReason(e.target.value)}
          options={(reasons ?? [])
            .filter((r) => r.is_active)
            .map((r) => ({ value: r.name, label: r.name }))}
        />
        <AppInput label="Ghi thêm" value={note} onChange={(e) => setNote(e.target.value)} />
      </div>
    </AppModal>
  );
}
