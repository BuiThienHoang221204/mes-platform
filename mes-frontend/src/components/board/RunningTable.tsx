"use client";

import { useEffect, useState } from "react";

import { LineCodes, LineState } from "@/components/board/LineState";
import { RunningActions } from "@/components/board/RunningActions";
import { DataTable, type Column } from "@/components/ui/DataTable";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { Pager } from "@/components/ui/Pager";
import { StatusPill } from "@/components/ui/StatusPill";
import { Tooltip } from "@/components/ui/Tooltip";
import { stationName } from "@/constants/stations";
import { useRunning } from "@/hooks/board/useBoard";
import type { RunningRow } from "@/types/board";
import { dur, nfmt } from "@/utils/format";

function TimeResult({ r }: { r: RunningRow }) {
  if (r.actual_sec == null) return <span className="text-fg-subtle">—</span>;
  if (r.on_time === false) return <StatusPill tone="danger">Quá giờ {dur(r.late_sec)}</StatusPill>;
  return <StatusPill tone="ok">Đạt</StatusPill>;
}

function AtStep({ r }: { r: RunningRow }) {
  const notAccepted = r.current_step == null;
  return (
    <span className="flex items-baseline gap-2">
      <span className="text-body text-fg">{stationName(r.current_step ?? 0)}</span>
      {notAccepted ? <span className="text-caption text-fg-subtle">chờ nhận</span> : null}
    </span>
  );
}

function QtyResult({ r }: { r: RunningRow }) {
  if (r.qty_ok == null) return <StatusPill tone="flat">Chưa chốt sổ</StatusPill>;
  if (r.qty_ok >= r.target_qty) return <StatusPill tone="ok">Đạt {nfmt(r.qty_ok)}</StatusPill>;
  return (
    <StatusPill tone="warn">
      Đạt {nfmt(r.qty_ok)}/{nfmt(r.target_qty)}
    </StatusPill>
  );
}

const HEAD: Column[] = [
  { label: "Mã lệnh", cellClassName: "font-mono text-body-lg" },
  { label: "Tên con hàng", className: "max-w-56" },
  { label: "Số lượng", right: true },
  { label: "Đang ở bước" },
  { label: "Chuyền" },
  { label: "TG yêu cầu", cellClassName: "tnum text-fg-muted" },
  { label: "TG chờ", right: true, cellClassName: "text-fg-muted" },
  { label: "TG thực tế", right: true },
  { label: "Hiện trạng chuyền" },
  { label: "Kết quả thời gian" },
  { label: "Sản lượng" },
];

export function RunningTable({
  withActions,
  onlyAssigned,
  fill,
}: {
  withActions?: boolean;
  onlyAssigned?: boolean;
  fill?: boolean;
}) {
  const [offset, setOffset] = useState(0);
  const { items, total, limit, isError, error, refetch, isLoading } = useRunning(offset);
  const rows = onlyAssigned ? items.filter((r) => (r.lines ?? []).length > 0) : items;

  useEffect(() => {
    if (total > 0 && offset >= total) setOffset(Math.max(0, total - limit));
  }, [total, offset, limit]);

  if (isError) return <ErrorState error={error} onRetry={() => refetch()} />;
  if (isLoading) return <EmptyState title="Đang tải bảng…" />;
  if (!rows.length) {
    return (
      <EmptyState
        title="Không có lệnh nào đang chạy chuyền"
        hint={onlyAssigned ? "Nhận lệnh rồi chia chuyền ở bước trước." : "Xưởng đang trống."}
      />
    );
  }

  const columns = withActions
    ? [...HEAD, { label: "", right: true, stickyRight: true } as Column]
    : HEAD;

  const body = rows.map((r) => {
    const wait = r.lines?.reduce((n, l) => Math.max(n, l.wait_sec), 0) ?? null;
    return {
      key: `${r.code}-${r.round_no}`,
      cells: [
        r.code,
        <Tooltip key="tooltip" content={r.product_name} className="truncate">
          <span className="truncate">{r.product_name}</span>
        </Tooltip>,
        nfmt(r.target_qty),
        <AtStep key="atstep" r={r} />,
        <LineCodes key="linecodes" lines={r.lines ?? []} />,
        <>
          {dur(r.required_sec)}
          <span className="block text-caption text-fg-subtle">
            vòng {r.round_no} · {nfmt(r.target_qty)}/{nfmt(r.quantity)}
          </span>
        </>,
        dur(wait),
        dur(r.actual_sec),
        <LineState key="linestate" row={r} />,
        <TimeResult key="timeresult" r={r} />,
        <QtyResult key="qtyresult" r={r} />,
        ...(withActions ? [<RunningActions key="runningactions" row={r} />] : []),
      ],
    };
  });

  return (
    <div className={fill ? "flex flex-col lg:min-h-0 lg:flex-1" : ""}>
      <DataTable columns={columns} rows={body} pad="lg" nowrap fill={fill} />
      <Pager
        offset={offset}
        shown={rows.length}
        total={total}
        limit={limit}
        onOffset={setOffset}
        unit="vòng"
        className="px-4"
      />
    </div>
  );
}
