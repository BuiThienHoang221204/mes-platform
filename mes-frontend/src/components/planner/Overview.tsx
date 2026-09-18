"use client";

import Link from "next/link";
import { useState } from "react";


import { Pager } from "@/components/ui/Pager";
import { AppCard } from "@/components/ui/AppCard";
import { Note } from "@/components/ui/Note";
import { EmptyState } from "@/components/ui/EmptyState";
import { QtyStat } from "@/components/ui/QtyStat";
import { MO_STATUS, type PillTone } from "@/constants/status";
import { STATIONS } from "@/constants/stations";
import { useCounts, useQueue, useRunning } from "@/hooks/board/useBoard";
import { useCatalogLines, useMoList } from "@/hooks/mo/useMo";
import { dur, nfmt } from "@/utils/format";

type Alert = { tone: PillTone; code: string; text: string };

export function Overview() {
  const { items: rows, total: runningTotal } = useRunning(0, 100);
  const { data: counts } = useCounts();
  const { items: khoQueue } = useQueue(0, 100);
  const { data: lines } = useCatalogLines();
  const { total: doneTotal } = useMoList({ status: MO_STATUS.COMPLETED });

  const late = rows.filter((r) => r.on_time === false);
  const reRound = rows.filter((r) => r.round_no > 1);
  const rework = khoQueue.filter((q) => q.round_no > 1);
  const busyLines = new Set(
    rows.flatMap((r) => (r.lines ?? []).filter((l) => l.current_kind).map((l) => l.line_code)),
  ).size;
  const heldLines = rows.flatMap((r) =>
    (r.lines ?? []).filter((l) => l.current_kind === "WAIT" && l.hold_reason),
  );

  const [alertOffset, setAlertOffset] = useState(0);
  const ALERT_PAGE = 5;

  const alerts: Alert[] = [
    ...rows
      .filter((r) => (r.lines ?? []).some((l) => l.current_kind === "WAIT" && l.hold_reason))
      .map((r) => {
        const held = (r.lines ?? []).filter((l) => l.current_kind === "WAIT" && l.hold_reason);
        return {
          tone: "danger" as const,
          code: r.code,
          text: `chuyền ${held.map((l) => l.line_code).join(", ")} đang dừng — ${held[0].hold_reason}. Dừng quá lâu thì cân nhắc trả về Bàn team leader chạy vòng mới.`,
        };
      }),
    ...late.map((r) => ({
      tone: "danger" as const,
      code: r.code,
      text: `quá giờ ${dur(r.late_sec)} — hạn mức vòng ${r.round_no} là ${dur(r.required_sec)} cho ${nfmt(r.target_qty)} pcs.`,
    })),
    ...rework.map((r) => ({
      tone: "warn" as const,
      code: r.code,
      text: `QC trả về Kho xuất, đang chờ nhận lại để chạy vòng ${r.round_no}.`,
    })),
    ...reRound
      .filter((r) => !late.some((l) => l.code === r.code))
      .map((r) => ({
        tone: "flat" as const,
        code: r.code,
        text: `đang chạy vòng ${r.round_no} — còn ${nfmt(r.target_qty)}/${nfmt(r.quantity)} pcs phải làm bù.`,
      })),
  ];

  return (
    <div className="flex min-h-0 flex-1 flex-col gap-4">
      <div className="grid shrink-0 gap-3 sm:grid-cols-2 lg:grid-cols-5">
        <QtyStat
          label="MO đang chạy"
          value={runningTotal}
          hint={rows.length < runningTotal
            ? `vòng chưa đóng · cảnh báo dưới soi ${rows.length} vòng đầu`
            : "vòng chưa đóng"}
          tone="accent"
        />
        <QtyStat
          label="Chuyền đang dùng"
          value={`${busyLines}/${lines?.length ?? 14}`}
          hint={heldLines.length ? `${heldLines.length} chuyền đang dừng` : "không chuyền nào dừng"}
          tone={heldLines.length ? "warn" : "plain"}
        />
        <QtyStat
          label="Làm lại"
          value={rework.length}
          hint="QC trả về Kho xuất"
          tone={rework.length ? "danger" : "plain"}
        />
        <QtyStat
          label="Đang ở vòng 2+"
          value={reRound.length}
          hint="chưa đủ số, làm bù"
          tone={reRound.length ? "warn" : "plain"}
        />
        <QtyStat label="Đã hoàn thành" value={doneTotal} hint="đã chốt đơn" tone="ok" />
      </div>

      <div className="grid min-h-0 flex-1 gap-5 lg:grid-cols-2">
        <AppCard
          title="Việc theo trạm"
          meta="chờ nhận · đang làm — bấm để mở trạm"
          flush
          className="flex min-h-0 flex-col"
          bodyClassName="flex min-h-0 flex-1 flex-col"
        >
          <ul className="no-scrollbar min-h-0 flex-1 overflow-y-auto">
            {STATIONS.map((s) => (
              <li key={s.no} className="border-b border-line last:border-b-0">
                <Link
                  href={s.route}
                  className="flex min-h-touch items-center gap-3 px-5 py-3 hover:bg-surface-2"
                >
                  <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-pill bg-surface-2 text-body-sm tnum text-fg-muted">
                    {s.no}
                  </span>
                  <span className="min-w-0 flex-1 truncate text-body text-fg">{s.name}</span>
                  <span className="shrink-0 text-right">
                    <span className="block text-body-lg tnum text-fg">
                      {counts?.counts?.[String(s.no)] ?? 0}
                    </span>
                    <span className="block text-caption text-fg-subtle">chờ nhận</span>
                  </span>
                  <span className="shrink-0 text-right">
                    <span
                      className={`block text-body-lg tnum ${
                        counts?.holding?.[String(s.no)] ? "text-accent" : "text-fg-subtle"
                      }`}
                    >
                      {counts?.holding?.[String(s.no)] ?? 0}
                    </span>
                    <span className="block text-caption text-fg-subtle">đang làm</span>
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        </AppCard>

        <AppCard
          title="Cần chú ý"
          meta={alerts.length ? `${alerts.length} việc` : undefined}
          flush
          className="flex min-h-0 flex-col"
          bodyClassName="flex min-h-0 flex-1 flex-col"
        >
          {!alerts.length ? (
            <EmptyState title="Không có gì bất thường" hint="Chưa lệnh nào quá giờ hay phải làm bù." />
          ) : (
            <div className="flex min-h-0 flex-1 flex-col">
              <div className="no-scrollbar min-h-0 flex-1 space-y-3 overflow-y-auto p-5">
                {alerts.slice(alertOffset, alertOffset + ALERT_PAGE).map((a, i) => (
                  <Note key={`${a.code}-${alertOffset + i}`} tone={a.tone}>
                    <strong className="font-mono">{a.code}</strong> — {a.text}
                  </Note>
                ))}
              </div>

              <Pager
                offset={alertOffset}
                shown={Math.min(ALERT_PAGE, alerts.length - alertOffset)}
                total={alerts.length}
                limit={ALERT_PAGE}
                onOffset={setAlertOffset}
              />
            </div>
          )}
        </AppCard>
      </div>
    </div>
  );
}
