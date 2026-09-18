"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { MagnifyingGlass } from "@/components/common/PhosphorIcons";
import { AppButton } from "@/components/ui/AppButton";
import { AppCard } from "@/components/ui/AppCard";
import { AppInput } from "@/components/ui/AppInput";
import { readMoCode } from "@/utils/moCode";

export function TraceLookup() {
  const router = useRouter();
  const [raw, setRaw] = useState("");

  const parsed = raw.trim() ? readMoCode(raw) : null;
  const code = parsed && "code" in parsed ? parsed.code : null;
  const go = () => {
    if (code) router.push(`/mos/${code}/trace`);
  };

  return (
    <AppCard title="Nhập hoặc quét mã lệnh">
      <div className="max-w-xl space-y-4">
        <AppInput
          mono
          value={raw}
          autoFocus
          onChange={(e) => setRaw(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") go();
          }}
          placeholder="M068820"
          hint="Quét bằng đầu đọc cũng được — Enter là tra luôn."
        />
        <AppButton
          variant="primary"
          onClick={go}
          disabled={!code}
          icon={<MagnifyingGlass size={28} weight="bold" />}
        >
          Tra cứu
        </AppButton>
      </div>
    </AppCard>
  );
}
