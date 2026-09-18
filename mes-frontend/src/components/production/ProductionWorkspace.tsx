"use client";

import { FinishPacking } from "@/components/packing/FinishPacking";
import { CloseBookForm } from "@/components/production/CloseBookForm";
import { LineSection } from "@/components/production/LineSection";
import { ShiftLog } from "@/components/production/ShiftLog";
import { AppButton } from "@/components/ui/AppButton";
import { AppCard } from "@/components/ui/AppCard";
import { ErrorState } from "@/components/ui/ErrorState";
import { QtyStat } from "@/components/ui/QtyStat";
import { StatusPill } from "@/components/ui/StatusPill";
import { useProductionActions, useTrace } from "@/hooks/production/useProduction";
import { today } from "@/utils/format";
import { reconcileBoxes } from "@/utils/packing";
import { nextAction } from "@/utils/stationFour";
import { currentRound, hourlyTotal, isPackingDone, isPackingStarted, isProductionClosed } from "@/utils/trace";

const TONE_RING = {
  accent: "border-accent bg-accent-soft",
  warn: "border-warn bg-warn-soft",
  danger: "border-danger bg-danger-soft",
  ok: "border-ok bg-ok-soft",
  flat: "border-line bg-surface-2",
} as const;

const TONE_TEXT = {
  accent: "text-accent",
  warn: "text-warn",
  danger: "text-danger",
  ok: "text-ok",
  flat: "text-fg-muted",
} as const;

function Task({
  no,
  title,
  desc,
  state,
  children,
  right,
}: {
  no: number;
  title: string;
  desc: string;
  state: "done" | "now" | "off";
  children?: React.ReactNode;
  right?: React.ReactNode;
}) {
  const dot =
    state === "done"
      ? "bg-ok text-ok-on"
      : state === "now"
        ? "bg-accent text-accent-on"
        : "bg-surface-2 text-fg-subtle";
  return (
    <div className="flex flex-wrap gap-3 border-b border-line py-4 last:border-b-0 sm:flex-nowrap sm:gap-4 sm:py-5">
      <span
        className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-pill text-body-sm tnum ${dot}`}
      >
        {no}
      </span>
      <div className="min-w-0 flex-1">
        <div className={`text-title ${state === "off" ? "text-fg-subtle" : "text-fg"}`}>{title}</div>
        <p className="mt-0.5 text-body-sm text-fg-muted">{desc}</p>
        {children ? <div className="mt-4">{children}</div> : null}
      </div>
      {right ? <div className="shrink-0 pl-11 sm:pl-0">{right}</div> : null}
    </div>
  );
}

export function ProductionWorkspace({ code }: { code: string }) {
  const { data: trace, isError, error, refetch } = useTrace(code);
  const a = useProductionActions(code);

  if (isError) return <ErrorState error={error} onRetry={() => refetch()} />;
  if (!trace) return <AppCard title={code}>Đang tải…</AppCard>;

  const round = currentRound(trace);
  if (!round) return <AppCard title={code}>Lệnh này chưa có vòng nào đang mở.</AppCard>;

  const box = reconcileBoxes(round, trace.pcs_per_box);
  const next = nextAction(trace, round, box);
  const sum = hourlyTotal(round);
  const closed = isProductionClosed(round);
  const packed = isPackingDone(round);
  const packStarted = isPackingStarted(round);
  const busy =
    a.assign.isPending || a.start.isPending || a.hold.isPending || a.logShift.isPending;

  const lines = round.lines ?? [];
  const everRan = lines.some((l) => l.run_sec > 0 || l.current_kind === "RUN");
  const held = lines.filter((l) => l.current_kind === "WAIT" && l.hold_reason_text);
  const canClose = everRan && !held.length;

  return (
    <div className="space-y-4 sm:space-y-5">
      <div
        className={`flex flex-wrap items-center gap-3 rounded-card border-2 px-4 py-4 sm:gap-4 sm:px-5 ${TONE_RING[next.tone]}`}
      >
        <div className="w-full sm:w-auto sm:min-w-[240px] sm:flex-1">
          <div
            className={`text-label uppercase tracking-wider ${TONE_TEXT[next.tone]}`}
          >
            {next.label}
          </div>
          <div className="text-title text-fg sm:text-h3">{next.title}</div>
          <p className="text-body-sm text-fg-muted">{next.hint}</p>
        </div>
        {next.goto ? (
          <AppButton
            variant="primary"
            className="w-full sm:w-auto"
            onClick={() =>
              document.getElementById(`sec-${next.goto}`)?.scrollIntoView({
                behavior: "smooth",
                block: "center",
              })
            }
          >
            Tới chỗ làm
          </AppButton>
        ) : null}
      </div>

      <AppCard
        title={`${trace.code} · ${trace.product_name}`}
        meta={trace.pcs_per_box ? `quy cách ${trace.pcs_per_box} pcs/thùng` : "không đóng thùng"}
        actions={<StatusPill tone="accent">Vòng {round.round_no}</StatusPill>}
      >
        <div className="grid grid-cols-2 gap-2 sm:gap-3 lg:grid-cols-4">
          <QtyStat label="Mục tiêu vòng" value={round.target_qty} unit="pcs" tone="accent" />
          <QtyStat label="Σ sản lượng giờ" value={sum} unit="pcs" />
          <QtyStat
            label="Đạt đã chốt"
            value={round.production?.qty_ok ?? "—"}
            tone={closed ? "ok" : "plain"}
          />
          <QtyStat
            label="Đã đóng thùng"
            value={box.packedPcs}
            unit="pcs"
            tone={box.diffPcs && closed ? "warn" : "plain"}
          />
        </div>
      </AppCard>

      <div id="sec-lines">
        <LineSection
          code={code}
          lines={lines}
          locked={closed}
          busy={busy}
          onAssign={(codes) => codes.forEach((c) => a.assign.mutate(c))}
          onStart={(codes) => codes.forEach((c) => a.start.mutate(c))}
          onHold={(codes, reason) => codes.forEach((c) => a.hold.mutate({ line: c, reason }))}
        />
      </div>

      {closed ? null : (
        <div id="sec-shift">
          <ShiftLog
            round={round}
            pcsPerBox={trace.pcs_per_box}
            box={box}
            packStarted={packStarted}
            busy={busy}
            onLog={(p) =>
              a.logShift.mutate({
                work_date: p.work_date,
                hourly: p.hourly,
                boxes: p.boxes,
              })
            }
          />
        </div>
      )}

      <div id="sec-end">
        <AppCard
          title="Kết thúc vòng"
          meta="làm đúng thứ tự — hai việc này không hoàn tác được"
          flush
        >
          <div className="px-4 sm:px-5">
            <Task
              no={1}
              title="Chốt sổ sản xuất"
              desc={
                closed
                  ? `Đã chốt · đạt ${round.production!.qty_ok} · hỏng ${round.production!.qty_ng} · thiếu ${round.production!.qty_short}`
                  : !everRan
                    ? "Khoá — phải có chuyền vào Đang lắp ráp trước đã."
                    : held.length
                      ? `Khoá — chuyền ${held.map((l) => l.line_code).join(", ")} đang dừng. Chốt lúc cả lệnh đứng im thì SL đạt là số của một ca chưa làm xong.`
                      : `Ba số đạt · hỏng · thiếu phải cộng đúng bằng ${round.target_qty}.`
              }
              state={closed ? "done" : canClose ? "now" : "off"}
              right={closed ? <StatusPill tone="ok">Đã chốt</StatusPill> : null}
            >
              {!closed && canClose ? (
                <CloseBookForm
                  targetQty={round.target_qty}
                  hourlySum={sum}
                  busy={a.close.isPending}
                  onSubmit={(p) => a.close.mutate(p)}
                />
              ) : null}
            </Task>

            <Task
              no={2}
              title="Kết thúc đóng thùng"
              desc={
                packed
                  ? `Đã kết thúc · đóng ${round.packing!.qty_packed} pcs`
                  : !closed
                    ? "Khoá — phải chốt sổ sản xuất trước, vì tới lúc đó mới biết có bao nhiêu hàng đạt để đối chiếu."
                    : "Sản xuất đã chốt sổ — kết thúc được rồi."
              }
              state={packed ? "done" : closed ? "now" : "off"}
              right={packed ? <StatusPill tone="ok">Đã xong</StatusPill> : null}
            >
              {closed && !packed ? (
                <FinishPacking
                  box={box}
                  pcsPerBox={trace.pcs_per_box}
                  busy={a.packHourly.isPending || a.packFinish.isPending}
                  onLogBoxes={(boxes) =>
                    a.packHourly.mutate({
                      work_date: today(),
                      slot_hour: new Date().getHours(),
                      boxes,
                    })
                  }
                  onFinish={(qty, note) => a.packFinish.mutate({ qty, note })}
                />
              ) : null}
            </Task>
          </div>
        </AppCard>
      </div>
    </div>
  );
}
