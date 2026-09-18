"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { Pause, Play, SealCheck } from "@/components/common/PhosphorIcons";
import { HoldLineModal } from "@/components/production/HoldLineModal";
import { AppButton } from "@/components/ui/AppButton";
import { FULL } from "@/constants/roles";
import { useProductionActions } from "@/hooks/production/useProduction";
import { useStationPerm } from "@/hooks/useStationPerm";
import type { RunningRow } from "@/types/board";

export function RunningActions({ row }: { row: RunningRow }) {
  const router = useRouter();
  const canWrite = useStationPerm(4) === FULL;
  const a = useProductionActions(row.code);
  const [holdOpen, setHoldOpen] = useState(false);

  if (!canWrite) return null;

  const lines = row.lines ?? [];
  const running = lines.filter((l) => l.current_kind === "RUN");
  const held = lines.filter((l) => l.current_kind === "WAIT" && l.hold_reason);
  const idle = lines.filter((l) => l.current_kind === "WAIT" && !l.hold_reason);
  const busy = a.start.isPending || a.hold.isPending;

  const openWork = () => router.push(`/production?step=work&mo=${row.code}`);

  if (row.production_closed_at) {
    return <span className="text-body-sm text-fg-subtle">đã chốt sổ</span>;
  }

  if (row.current_step == null || row.current_step < 4) return null;

  if (!lines.length) {
    return (
      <AppButton size="sm" variant="primary" onClick={openWork}>
        Chia chuyền
      </AppButton>
    );
  }

  if (held.length) {
    return (
      <AppButton
        size="sm"
        variant="primary"
        disabled={busy}
        onClick={() => held.forEach((l) => a.start.mutate(l.line_code))}
        icon={<Play size={18} weight="fill" />}
      >
        Chạy lại {held.length > 1 ? `${held.length} chuyền` : held[0].line_code}
      </AppButton>
    );
  }

  if (idle.length && !running.length) {
    return (
      <AppButton
        size="sm"
        variant="primary"
        disabled={busy}
        onClick={() => idle.forEach((l) => a.start.mutate(l.line_code))}
        icon={<Play size={18} weight="fill" />}
      >
        Cho chạy {idle.length > 1 ? `${idle.length} chuyền` : idle[0].line_code}
      </AppButton>
    );
  }

  return (
    <>
      <div className="flex justify-end gap-2">
        {idle.length ? (
          <AppButton
            size="sm"
            className="min-w-32"
            disabled={busy}
            onClick={() => idle.forEach((l) => a.start.mutate(l.line_code))}
            icon={<Play size={18} weight="fill" />}
          >
            Cho chạy {idle[0].line_code}
          </AppButton>
        ) : null}
        <AppButton
          size="sm"
          variant="danger"
          className="min-w-32"
          disabled={busy}
          onClick={() => setHoldOpen(true)}
          icon={<Pause size={18} weight="fill" />}
        >
          Dừng
        </AppButton>
        <AppButton
          size="sm"
          variant="primary"
          className="min-w-32"
          disabled={idle.length > 0}
          title={idle.length ? "Còn chuyền chưa vào Đang lắp ráp" : undefined}
          onClick={openWork}
          icon={<SealCheck size={18} weight="fill" />}
        >
          Hoàn thành
        </AppButton>
      </div>

      <HoldLineModal
        open={holdOpen}
        code={row.code}
        running={running.map((l) => l.line_code)}
        busy={busy}
        onClose={() => setHoldOpen(false)}
        onHold={(codes, reason) => codes.forEach((line) => a.hold.mutate({ line, reason }))}
      />
    </>
  );
}
