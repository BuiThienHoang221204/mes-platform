"use client";

import { useCallback, useEffect, useState } from "react";

import { QrCode, Scan } from "@/components/common/PhosphorIcons";
import { CameraScanModal } from "@/components/scan/CameraScanModal";
import { ScanFeedback } from "@/components/scan/ScanFeedback";
import { AppButton } from "@/components/ui/AppButton";
import { useScan } from "@/hooks/scan/useScan";
import { useScanInput } from "@/hooks/useScanInput";
import { useScanStore } from "@/stores/useScanStore";

export function ScanBar({ station, hint }: { station: number; hint: string }) {
  const scan = useScan(station);
  const draft = useScanStore((s) => s.draft);
  const [camOpen, setCamOpen] = useState(false);
  const { ref, onKeyDown } = useScanInput((raw) => scan.mutate(raw), !scan.isPending && !camOpen);

  useEffect(() => {
    if (!draft || !ref.current) return;
    ref.current.value = draft;
    ref.current.focus();
  }, [draft, ref]);

  const submit = () => {
    const el = ref.current;
    const raw = el?.value.trim();
    if (!raw) return;
    el!.value = "";
    scan.mutate(raw);
  };

  // Phụ thuộc `scan.mutate` chứ không phải cả `scan`: đối tượng mutation đổi danh
  // tính mỗi lần render (isPending, data…), còn `mutate` thì ổn định. Lấy cả đối
  // tượng làm dependency là mọi effect bên dưới chạy lại liên tục — chính chỗ đó
  // làm camera bị tắt rồi bật lại giữa chừng.
  const send = scan.mutate;
  const fromCamera = useCallback((raw: string) => send(raw), [send]);
  const closeCam = useCallback(() => setCamOpen(false), []);

  return (
    <div className="space-y-3 rounded-card border border-dashed border-accent bg-surface p-3 sm:p-4">
      <div className="flex flex-wrap items-center gap-2 sm:gap-3">
        <input
          ref={ref}
          onKeyDown={onKeyDown}
          disabled={scan.isPending}
          placeholder="Quét / nhập mã lệnh…"
          autoComplete="off"
          spellCheck={false}
          className="min-h-touch w-full min-w-0 basis-full rounded-field border border-accent bg-surface-2 px-4 font-mono text-body-lg tracking-wide text-fg placeholder:font-sans placeholder:text-fg-subtle sm:w-auto sm:flex-1 sm:basis-auto"
        />
        <AppButton
          className="flex-1 sm:flex-none"
          onClick={() => setCamOpen(true)}
          disabled={scan.isPending}
          icon={<Scan size={24} />}
        >
          Scan MO
        </AppButton>
        <AppButton
          variant="primary"
          className="flex-1 sm:flex-none"
          onClick={submit}
          disabled={scan.isPending}
          icon={<QrCode size={28} weight="bold" />}
        >
          {scan.isPending ? "Đang nhận…" : "Nhận"}
        </AppButton>
      </div>

      <ScanFeedback station={station} />
      <p className="text-caption text-fg-subtle">{hint}</p>

      <CameraScanModal open={camOpen} onClose={closeCam} onRead={fromCamera} />
    </div>
  );
}
