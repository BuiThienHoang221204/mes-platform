import type { ReactNode } from "react";

import type { PillTone } from "@/constants/status";
import {
  MO_STATUS_LABEL,
  MO_STATUS_TONE,
  QC_RESULT_LABEL,
  SEGMENT_KIND_LABEL,
  type MoStatusValue,
  type QcResultValue,
} from "@/constants/status";

const TONE: Record<PillTone, string> = {
  accent: "bg-accent-soft text-accent",
  ok: "bg-ok-soft text-ok",
  warn: "bg-warn-soft text-warn",
  danger: "bg-danger-soft text-danger",
  flat: "bg-surface-2 text-fg-muted",
};

type Props = {
  tone?: PillTone;
  live?: boolean;
  children: ReactNode;
};

export function StatusPill({ tone = "flat", live, children }: Props) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 whitespace-nowrap rounded-pill px-3 py-1 text-badge ${TONE[tone]}`}
    >
      {live ? <span className="h-2 w-2 animate-pulse rounded-pill bg-current" /> : null}
      {children}
    </span>
  );
}

export function MoStatusPill({ status }: { status: MoStatusValue }) {
  return (
    <StatusPill tone={MO_STATUS_TONE[status]} live={status === "PROCESSING"}>
      {MO_STATUS_LABEL[status]}
    </StatusPill>
  );
}

export function QcResultPill({ result }: { result: QcResultValue }) {
  return (
    <StatusPill tone={result === "PASS" ? "ok" : "danger"}>{QC_RESULT_LABEL[result]}</StatusPill>
  );
}

export function SegmentPill({ kind }: { kind: "WAIT" | "RUN" }) {
  return (
    <StatusPill tone={kind === "RUN" ? "ok" : "warn"} live={kind === "RUN"}>
      {SEGMENT_KIND_LABEL[kind]}
    </StatusPill>
  );
}
