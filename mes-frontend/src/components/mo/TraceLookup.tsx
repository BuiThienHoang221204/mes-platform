"use client";

import { useRouter } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";

import { MagnifyingGlass, Scan } from "@/components/common/PhosphorIcons";
import { CameraScanModal } from "@/components/scan/CameraScanModal";
import { AppButton } from "@/components/ui/AppButton";
import { AppCard } from "@/components/ui/AppCard";
import { AppInput } from "@/components/ui/AppInput";
import { readMoCode } from "@/utils/moCode";

export function TraceLookup() {
  const router = useRouter();
  const [raw, setRaw] = useState("");
  const [camOpen, setCamOpen] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const parsed = raw.trim() ? readMoCode(raw) : null;
  const code = parsed && "code" in parsed ? parsed.code : null;

  const go = useCallback(() => {
    if (code) router.push(`/mos/${code}/trace`);
  }, [code, router]);

  // Auto-navigate khi quét barcode (không cần Enter)
  useEffect(() => {
    if (!code) return;
    const id = setTimeout(go, 300);
    return () => clearTimeout(id);
  }, [code, go]);

  return (
    <AppCard title="Nhập hoặc quét mã lệnh">
      <div className="max-w-xl">
        <div className="flex items-stretch gap-2">
          <AppInput
            ref={inputRef}
            mono
            value={raw}
            onChange={(e) => setRaw(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") go();
            }}
            placeholder="M068820"
            // hint="Quét bằng đầu đọc cũng được — Enter là tra luôn."
            className="flex-1"
          />
          <AppButton
            variant="outline"
            icon={<Scan size={20} />}
            className="min-h-touch"
            onClick={() => setCamOpen(true)}
          />
          <AppButton
            variant="primary"
            onClick={go}
            disabled={!code}
            icon={<MagnifyingGlass size={20} weight="bold" />}
            className="min-h-touch"
          />
        </div>
      </div>

      <CameraScanModal
        open={camOpen}
        onClose={() => setCamOpen(false)}
        onRead={(scanned) => {
          setRaw(scanned);
          setCamOpen(false);
        }}
      />
    </AppCard>
  );
}
