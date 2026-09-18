"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect } from "react";

import { RunningTable } from "@/components/board/RunningTable";
import { PageHeader } from "@/components/common/PageHeader";
import { StepStrip } from "@/components/common/StepStrip";
import { MoCreateForm } from "@/components/mo/MoCreateForm";
import { MoTable } from "@/components/mo/MoTable";
import { Overview } from "@/components/planner/Overview";
import { AppCard } from "@/components/ui/AppCard";
import { PLANNER } from "@/constants/roles";
import {
  PLANNER_ROUTE,
  PLANNER_STEPS,
  PLANNER_TRACE_STEP,
  TRACE_ROUTE,
  resolvePlannerStep,
} from "@/constants/plannerSteps";
import { useSessionStore } from "@/stores/useSessionStore";
import type { MoStatus } from "@/types/mo";

function PlannerBody() {
  const params = useSearchParams();
  const router = useRouter();
  const roles = useSessionStore((s) => s.roles);
  const step = resolvePlannerStep(params.get("step"));
  const filter = params.get("status") as MoStatus | null;
  const wasTrace = params.get("step") === PLANNER_TRACE_STEP;

  useEffect(() => {
    if (wasTrace) router.replace(TRACE_ROUTE);
  }, [wasTrace, router]);

  if (!roles.includes(PLANNER)) {
    return (
      <div className="mx-auto max-w-lg py-16 text-center">
        <h1 className="text-h2">Chỉ điều độ mở được màn này</h1>
        <p className="mt-2 text-body text-fg-muted">Tạo và chốt lệnh là việc của phòng kế hoạch.</p>
      </div>
    );
  }

  const go = (id: string) =>
    router.replace(id === PLANNER_STEPS[0].id ? PLANNER_ROUTE : `${PLANNER_ROUTE}?step=${id}`);

  const setFilter = (s: MoStatus | null) =>
    router.replace(`${PLANNER_ROUTE}?step=book${s ? `&status=${s}` : ""}`);

  const fitsOneScreen = step === "dash";

  return (
    <div className={fitsOneScreen ? "flex h-full min-h-0 flex-col" : ""}>
      <PageHeader
        kicker="Planner · Điều độ"
        title={PLANNER_STEPS.find((s) => s.id === step)?.name ?? ""}
        subtitle="Toàn quyền mọi trạm — vai điều độ, phải vào được mọi chỗ khi có sự cố."
      />

      <div
        className={
          fitsOneScreen ? "flex min-h-0 flex-1 flex-col gap-5" : "space-y-5"
        }
      >
        <StepStrip steps={PLANNER_STEPS} active={step} onPick={go} />

        {step === "dash" ? <Overview /> : null}
        {step === "create" ? <MoCreateForm /> : null}

        {step === "book" ? (
          <MoTable status={filter ?? undefined} onStatus={setFilter} />
        ) : null}

        {step === "board" ? (
          <AppCard title="Bảng đang chạy" meta="tự làm mới mỗi 10 giây" flush>
            <RunningTable withActions />
          </AppCard>
        ) : null}
      </div>
    </div>
  );
}

export default function PlannerPage() {
  return (
    <Suspense fallback={null}>
      <PlannerBody />
    </Suspense>
  );
}
