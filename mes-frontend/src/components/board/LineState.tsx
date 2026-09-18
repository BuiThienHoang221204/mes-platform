import { StatusPill } from "@/components/ui/StatusPill";
import type { BoardLine, RunningRow } from "@/types/board";

export function LineCodes({ lines }: { lines: BoardLine[] }) {
  if (!lines.length) return <span className="text-fg-subtle">chưa chia</span>;
  return <span className="font-mono text-body">{lines.map((l) => l.line_code).join(", ")}</span>;
}

export function LineState({ row }: { row: RunningRow }) {
  const lines = row.lines ?? [];

  if (row.production_closed_at) return <StatusPill tone="flat">Hoàn thành</StatusPill>;
  if (!lines.length) return <span className="text-fg-subtle">—</span>;

  const held = lines.filter((l) => l.current_kind === "WAIT" && l.hold_reason);
  if (held.length) {
    return (
      <span className="space-y-1">
        <StatusPill tone="danger">
          ĐANG DỪNG {held.map((l) => l.line_code).join(", ")}
        </StatusPill>
        <span className="block text-caption text-fg-muted">{held[0].hold_reason}</span>
      </span>
    );
  }

  if (lines.some((l) => l.current_kind === "RUN")) {
    return (
      <StatusPill tone="ok" live>
        Đang lắp ráp
      </StatusPill>
    );
  }

  return <StatusPill tone="warn">Chờ xử lý</StatusPill>;
}
