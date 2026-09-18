"use client";

import { AppCard } from "@/components/ui/AppCard";
import { DataTable, type Column } from "@/components/ui/DataTable";
import { StatusPill } from "@/components/ui/StatusPill";
import type { StepTotal, TraceRound } from "@/types/trace";
import { dur } from "@/utils/format";

const hhmm = (iso: string | null) => (iso ? iso.slice(11, 16) : "—");

const COLUMNS: Column[] = [
  { label: "Bước" },
  { label: "Ai nhận", cellClassName: "text-fg-muted" },
  { label: "Nhận lúc", cellClassName: "tnum text-fg-muted" },
  { label: "Mất bao lâu", cellClassName: "tnum" },
];

type Props = {
  round: TraceRound;
  totals: StepTotal[];
};

export function StepTable({ round, totals }: Props) {
  const roundsOf = (stepNo: number) => totals.find((t) => t.step_no === stepNo)?.rounds ?? 1;

  const body = round.steps.map((s) => {
    const n = roundsOf(s.step_no);
    const sec = s.closed_at
      ? (Date.parse(s.closed_at) - Date.parse(s.accepted_at)) / 1000
      : null;
    return {
      key: String(s.step_no),
      cells: [
        <span key="span" className="flex items-center gap-2 text-body">
          {s.step_no} · {s.name}
          {n > 1 ? <StatusPill tone="flat">{n} vòng</StatusPill> : null}
        </span>,
        s.accepted_by ?? "—",
        hhmm(s.accepted_at),
        sec == null ? "đang giữ" : dur(sec),
      ],
    };
  });

  return (
    <AppCard
      title="2 · Đi qua các bước — mỗi vòng một bảng"
      meta={`đang xem vòng ${round.round_no}`}
      flush
    >
      <DataTable columns={COLUMNS} rows={body} />
      <p className="border-t border-line px-4 py-3 text-body-sm text-fg-muted">
        Bảng cộng dồn qua <strong className="text-fg">mọi vòng</strong>, kèm chú thích khi bước đó
        chạy nhiều lần. Chỉ đọc vòng hiện tại thì lệnh đi qua Setup hai lần mà vòng cuối bắt đầu từ
        Bàn team leader sẽ hiện dấu gạch — nhìn vào tưởng chưa từng canh máy.
      </p>
    </AppCard>
  );
}
