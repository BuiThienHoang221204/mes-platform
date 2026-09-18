"use client";

import { useState } from "react";

import { EventLogTable } from "@/components/mo/EventLogTable";
import { RoundDetail } from "@/components/mo/RoundDetail";
import { RoundTable } from "@/components/mo/RoundTable";
import { StepTable } from "@/components/mo/StepTable";
import { PageHeader } from "@/components/common/PageHeader";
import { AppButton } from "@/components/ui/AppButton";
import { AppCard } from "@/components/ui/AppCard";
import { ErrorState } from "@/components/ui/ErrorState";
import { QtyStat } from "@/components/ui/QtyStat";
import { useTraceMo } from "@/hooks/mo/useMo";

export function TraceDetail({ code }: { code: string }) {
  const { data, isError, error, refetch, isLoading } = useTraceMo(code);
  const [openRound, setOpenRound] = useState<number | null>(null);

  if (isError) return <ErrorState error={error} onRetry={() => refetch()} />;
  if (isLoading || !data) return <AppCard title={code}>Đang tải…</AppCard>;

  const shown = data.rounds.find((r) => r.round_no === openRound) ?? data.rounds.at(-1);
  const p = data.progress;
  const scrap = p.quantity ? Math.round((p.qty_ng_total / p.quantity) * 1000) / 10 : 0;

  return (
    <>
      <PageHeader
        kicker="Tra cứu"
        title={`Truy cứu lệnh · ${data.code}`}
        subtitle="Bốn tầng: các vòng → đi qua các bước → năng suất chuyền và sản lượng giờ → nhật ký đầy đủ."
      />

      <div className="space-y-5">
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
          <QtyStat label={data.code} value={p.quantity} unit="pcs" hint="số lượng kế hoạch" />
          <QtyStat label="Đã xong" value={p.qty_done} unit="pcs" tone="ok" hint="đã đóng thùng" />
          <QtyStat
            label="Còn lại"
            value={p.qty_remain}
            unit="pcs"
            tone={p.qty_remain ? "warn" : "ok"}
            hint="mục tiêu vòng đang chạy"
          />
          <QtyStat
            label="Hỏng cộng dồn"
            value={p.qty_ng_total}
            unit="pcs"
            tone={p.qty_ng_total ? "danger" : "plain"}
            hint={`tỷ lệ phế ${scrap}%`}
          />
          <QtyStat
            label="Vòng hiện tại"
            value={data.rounds.length}
            tone="accent"
            hint={p.rounds_done ? `đã chốt ${p.rounds_done} vòng` : "chưa vòng nào chốt"}
          />
        </div>

        <RoundTable rounds={data.rounds} />

        <div className="flex flex-wrap gap-2">
          {data.rounds.map((r) => (
            <AppButton
              key={r.round_no}
              size="sm"
              variant={shown?.round_no === r.round_no ? "primary" : "outline"}
              onClick={() => setOpenRound(r.round_no)}
            >
              Chi tiết vòng {r.round_no}
            </AppButton>
          ))}
        </div>

        {shown ? (
          <>
            <StepTable round={shown} totals={data.step_totals} />
            <RoundDetail code={data.code} round={shown} pcsPerBox={data.pcs_per_box} />
          </>
        ) : null}

        <EventLogTable code={data.code} first={data.events} total={data.events_total} />
      </div>
    </>
  );
}
