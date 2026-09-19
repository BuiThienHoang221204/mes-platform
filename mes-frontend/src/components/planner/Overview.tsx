"use client";

import Link from "next/link";
import { useState } from "react";


import { Pager } from "@/components/ui/Pager";
import { AppCard } from "@/components/ui/AppCard";
import { Note } from "@/components/ui/Note";
import { EmptyState } from "@/components/ui/EmptyState";
import { QtyStat } from "@/components/ui/QtyStat";
import { type PillTone } from "@/constants/status";
import { STATIONS } from "@/constants/stations";
import { useCounts, useOverview } from "@/hooks/board/useBoard";
import type { OverviewAlert } from "@/types/board";
import { dur, nfmt } from "@/utils/format";

type Alert = { tone: PillTone; code: string; text: string };

/* Máy chủ gửi DỮ LIỆU cảnh báo, câu chữ dựng ở đây.
 *
 *  Giữ lời ở frontend vì lời là thứ hay sửa nhất — đổi một câu không nên phải
 *  triển khai lại backend. Đổi lại gói tin cũng gọn hơn: `{kind, code, round_no,
 *  lines}` tốn ~70 byte, cùng nội dung viết thành câu tốn hơn gấp đôi. */
const TONE: Record<OverviewAlert["kind"], PillTone> = {
  HOLD: "danger",
  LATE: "danger",
  REWORK: "warn",
  RE_ROUND: "flat",
};

function alertText(a: OverviewAlert): string {
  switch (a.kind) {
    case "HOLD":
      return `chuyền ${(a.lines ?? []).join(", ")} đang dừng — ${a.reason}. Dừng quá lâu thì cân nhắc trả về Bàn team leader chạy vòng mới.`;
    case "LATE":
      return `quá giờ ${dur(a.late_sec ?? null)} — hạn mức vòng ${a.round_no} là ${dur(a.required_sec ?? null)} cho ${nfmt(a.target_qty ?? 0)} pcs.`;
    case "REWORK":
      return `QC trả về Kho xuất, đang chờ nhận lại để chạy vòng ${a.round_no}.`;
    case "RE_ROUND":
      return `đang chạy vòng ${a.round_no} — còn ${nfmt(a.target_qty ?? 0)}/${nfmt(a.quantity ?? 0)} pcs phải làm bù.`;
  }
}

export function Overview() {
  const { data: ov } = useOverview();
  const { data: counts } = useCounts();

  const [alertOffset, setAlertOffset] = useState(0);
  const ALERT_PAGE = 5;

  const alerts: Alert[] = (ov?.alerts ?? []).map((a) => ({
    tone: TONE[a.kind],
    code: a.code,
    text: alertText(a),
  }));

  const runningTotal = ov?.running_rounds ?? 0;
  const busyLines = ov?.lines_busy ?? 0;
  const heldCount = ov?.lines_held ?? 0;
  const reworkCount = ov?.rework ?? 0;
  const reRoundCount = ov?.re_round ?? 0;
  const doneTotal = ov?.completed ?? 0;
  const alertsTotal = ov?.alerts_total ?? 0;

  return (
    <div className="flex flex-col gap-4 lg:min-h-0 lg:flex-1">
      <div className="grid shrink-0 grid-cols-2 gap-2 sm:grid-cols-3 sm:gap-3 lg:grid-cols-5">
        <QtyStat
          label="MO đang chạy"
          value={runningTotal}
          hint="vòng chưa đóng"
          tone="accent"
        />
        <QtyStat
          label="Chuyền đang dùng"
          value={`${busyLines}/${ov?.lines_total ?? 14}`}
          hint={heldCount ? `${heldCount} chuyền đang dừng` : "không chuyền nào dừng"}
          tone={heldCount ? "warn" : "plain"}
        />
        <QtyStat
          label="Làm lại"
          value={reworkCount}
          hint="QC trả về Kho xuất"
          tone={reworkCount ? "danger" : "plain"}
        />
        <QtyStat
          label="Đang ở vòng 2+"
          value={reRoundCount}
          hint="chưa đủ số, làm bù"
          tone={reRoundCount ? "warn" : "plain"}
        />
        <QtyStat label="Đã hoàn thành" value={doneTotal} hint="đã chốt đơn" tone="ok" />
      </div>

      <div className="grid gap-4 lg:min-h-0 lg:flex-1 lg:gap-5 lg:grid-cols-2">
        <AppCard
          title="Việc theo trạm"
          meta="chờ nhận · đang làm — bấm để mở trạm"
          flush
          className="flex flex-col lg:min-h-0"
          bodyClassName="flex flex-col lg:min-h-0 lg:flex-1"
        >
          <ul className="no-scrollbar lg:min-h-0 lg:flex-1 lg:overflow-y-auto">
            {STATIONS.map((s) => (
              <li key={s.no} className="border-b border-line last:border-b-0">
                <Link
                  href={s.route}
                  className="flex min-h-touch items-center gap-2 px-4 py-3 hover:bg-surface-2 sm:gap-3 sm:px-5"
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
          meta={alertsTotal ? `${alertsTotal} việc` : undefined}
          flush
          className="flex flex-col lg:min-h-0"
          bodyClassName="flex flex-col lg:min-h-0 lg:flex-1"
        >
          {!alerts.length ? (
            <EmptyState title="Không có gì bất thường" hint="Chưa lệnh nào quá giờ hay phải làm bù." />
          ) : (
            <div className="flex flex-col lg:min-h-0 lg:flex-1">
              <div className="no-scrollbar space-y-3 p-4 sm:p-5 lg:min-h-0 lg:flex-1 lg:overflow-y-auto">
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
