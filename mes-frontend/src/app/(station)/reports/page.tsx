"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { Suspense } from "react";

import { PageHeader } from "@/components/common/PageHeader";
import { StepStrip } from "@/components/common/StepStrip";
import { MoProgress } from "@/components/reports/MoProgress";
import { SlotRanking } from "@/components/reports/SlotRanking";
import { StepCounts } from "@/components/reports/StepCounts";
import { REPORT_ROUTE, REPORT_STEPS, resolveReportStep } from "@/constants/reportSteps";

function ReportsBody() {
  const params = useSearchParams();
  const router = useRouter();
  const step = resolveReportStep(params.get("step"));
  const here = REPORT_STEPS.find((s) => s.id === step);

  const go = (id: string) =>
    router.replace(id === REPORT_STEPS[0].id ? REPORT_ROUTE : `${REPORT_ROUTE}?step=${id}`);

  return (
    <div className="flex flex-col lg:h-full lg:min-h-0">
      <PageHeader kicker="Xem chung" title={here?.name ?? ""} subtitle={here?.sub} />

      <div className="flex flex-col gap-4 lg:min-h-0 lg:flex-1 lg:gap-5">
        <div className="shrink-0">
          <StepStrip steps={REPORT_STEPS} active={step} onPick={go} />
        </div>

        {step === "progress" ? <MoProgress /> : null}
        {step === "hourly" ? <SlotRanking /> : null}
        {step === "steps" ? <StepCounts /> : null}
      </div>
    </div>
  );
}

export default function ReportsPage() {
  return (
    <Suspense fallback={null}>
      <ReportsBody />
    </Suspense>
  );
}
