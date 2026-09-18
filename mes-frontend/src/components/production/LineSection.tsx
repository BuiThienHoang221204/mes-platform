"use client";

import { useState } from "react";

import { Pause, Play } from "@/components/common/PhosphorIcons";
import { HoldLineModal } from "@/components/production/HoldLineModal";
import { AppButton } from "@/components/ui/AppButton";
import { AppCard } from "@/components/ui/AppCard";
import { useLines } from "@/hooks/production/useProduction";
import type { TraceLine } from "@/types/trace";

type Props = {
  code: string;
  lines: TraceLine[];
  /** Vòng đã chốt sổ SX — chuyền đóng hết, không thao tác nữa. */
  locked: boolean;
  busy?: boolean;
  onAssign: (lineCodes: string[]) => void;
  onStart: (lineCodes: string[]) => void;
  onHold: (lineCodes: string[], reason: string) => void;
};

const STATE = {
  RUN: { label: "đang lắp ráp", cls: "border-ok bg-ok-soft text-ok" },
  HOLD: { label: "đang dừng", cls: "border-danger bg-danger-soft text-danger" },
  WAIT: { label: "chờ xử lý", cls: "border-accent bg-accent-soft text-accent" },
  DONE: { label: "đã đóng", cls: "border-line-strong bg-surface-2 text-fg-muted" },
} as const;

export function LineSection({ code, lines, locked, busy, onAssign, onStart, onHold }: Props) {
  const { data: catalog } = useLines();
  const [picked, setPicked] = useState<string[]>([]);
  const [holdOpen, setHoldOpen] = useState(false);

  const assigned = new Map(lines.map((l) => [l.line_code, l]));
  const running = lines.filter((l) => l.current_kind === "RUN");
  const held = lines.filter((l) => l.current_kind === "WAIT" && l.hold_reason_text);
  const idle = lines.filter((l) => l.current_kind === "WAIT" && !l.hold_reason_text);
  const startable = [...held, ...idle].map((l) => l.line_code);

  // Chốt sổ xong thì `current_kind` là null vì mọi đoạn đã đóng. Rơi về "chờ xử
  // lý" như trước là nói sai: chuyền không chờ gì nữa, nó đã đóng cùng một mốc.
  const stateOf = (l: TraceLine) =>
    locked
      ? STATE.DONE
      : l.current_kind === "RUN"
        ? STATE.RUN
        : l.hold_reason_text
          ? STATE.HOLD
          : STATE.WAIT;

  const toggle = (c: string) =>
    setPicked((p) => (p.includes(c) ? p.filter((x) => x !== c) : [...p, c]));

  return (
    <AppCard
      title="Chuyền"
      meta={
        lines.length
          ? `${lines.length} chuyền · ${running.length} đang lắp ráp`
          : "chưa chia chuyền"
      }
    >
      <div className="grid grid-cols-3 gap-2 sm:grid-cols-5 sm:gap-3 lg:grid-cols-7">
        {(catalog ?? [])
          .filter((l) => l.is_active)
          .map((l) => {
            const on = assigned.get(l.code);
            const st = on ? stateOf(on) : null;
            const isPicked = picked.includes(l.code);
            return (
              <button
                key={l.code}
                type="button"
                disabled={!!on || locked}
                onClick={() => toggle(l.code)}
                className={`flex min-h-[56px] flex-col items-center justify-center gap-0.5 rounded-field border px-2 disabled:cursor-not-allowed ${
                  st
                    ? st.cls
                    : isPicked
                      ? "border-accent bg-accent text-accent-on"
                      : "border-line-strong bg-surface text-fg"
                }`}
              >
                <span className="font-mono text-body-lg">{l.code}</span>
                <span className="text-caption">
                  {st ? st.label : isPicked ? "sẽ thêm" : "trống"}
                </span>
              </button>
            );
          })}
      </div>

      {locked ? (
        <p className="mt-4 text-body-sm text-fg-muted">
          Đã chốt sổ sản xuất — mọi chuyền đóng cùng một mốc, không thêm hay chạy lại được nữa.
        </p>
      ) : (
        <>
          <div className="mt-4 flex flex-wrap gap-2 sm:gap-3">
            {picked.length ? (
              <AppButton
                variant="primary"
                disabled={busy}
                onClick={() => {
                  onAssign(picked);
                  setPicked([]);
                }}
              >
                Thêm {picked.length} chuyền
              </AppButton>
            ) : null}

            {startable.length ? (
              <AppButton
                variant="primary"
                disabled={busy}
                icon={<Play size={20} weight="fill" />}
                onClick={() => onStart(startable)}
              >
                {held.length ? "Chạy lại" : "Cho chạy"} {startable.length} chuyền
              </AppButton>
            ) : null}

            {running.length ? (
              <AppButton
                variant="danger"
                disabled={busy}
                icon={<Pause size={20} weight="fill" />}
                onClick={() => setHoldOpen(true)}
              >
                Dừng chuyền
              </AppButton>
            ) : null}
          </div>

          <p className="mt-3 text-body-sm text-fg-subtle">
            {lines.length
              ? "Thời gian chờ đếm khi chuyền ở Chờ xử lý, dừng khi sang Đang lắp ráp. Bấm Dừng thì đồng hồ thực tế đứng lại."
              : "Một chuyền là dây chuyền có nhiều chỗ ngồi — lệnh ít linh kiện chỉ dùng vài chỗ, chỗ còn lại chạy lệnh khác."}
          </p>
        </>
      )}

      <HoldLineModal
        open={holdOpen}
        code={code}
        running={running.map((l) => l.line_code)}
        busy={busy}
        onClose={() => setHoldOpen(false)}
        onHold={onHold}
      />
    </AppCard>
  );
}
