"use client";

import type { ReactNode } from "react";

import { Clock } from "@/components/common/PhosphorIcons";
import { AppCard } from "@/components/ui/AppCard";
import { DataTable, type Column } from "@/components/ui/DataTable";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { RoundBadge } from "@/components/ui/RoundBadge";
import { useAtStation } from "@/hooks/board/useBoard";
import type { AtStationRow } from "@/types/board";
import { boxLabel, dur, nfmt } from "@/utils/format";

type Props = {
  station: number;
  title?: string;
  fill?: boolean;
  action?: (row: AtStationRow) => ReactNode;
};

export function AtStationTable({ station, title, fill = true, action }: Props) {
  const { items: rows, total, isLoading, isError, error, refetch } = useAtStation(station);
  const hidden = total - rows.length;
  const showBoxes = station === 5;

  const columns: Column[] = [
    { label: "Mã lệnh", cellClassName: "font-mono text-body-lg" },
    { label: "Con hàng" },
    { label: "SL cần làm", right: true },
    ...(showBoxes ? [{ label: "Nhận về", right: true } as Column] : []),
    { label: "Vòng" },
    { label: "Nhận lúc", cellClassName: "text-body-sm text-fg-muted" },
    { label: "Đang giữ", cellClassName: "text-body-sm tnum text-fg-muted" },
    ...(action ? [{ label: "", right: true, stickyRight: true } as Column] : []),
  ];

  const body = rows.map((r) => ({
    key: r.code,
    cells: [
      r.code,
      r.product_name,
      nfmt(r.target_qty),
      ...(showBoxes
        ? [
            <>
              <span className="block text-body tnum text-fg">
                {boxLabel(r.qty_packed ?? 0, r.pcs_per_box)}
              </span>
              <span className="block text-caption tnum text-fg-subtle">
                {nfmt(r.qty_packed ?? 0)} pcs
              </span>
            </>,
          ]
        : []),
      <RoundBadge key="roundbadge" round={r.round_no} target={r.target_qty} quantity={r.quantity} />,
      `${r.accepted_at?.slice(11, 16) ?? "—"} · ${r.accepted_by}`,
      dur(r.holding_sec),
      ...(action ? [action(r)] : []),
    ],
  }));

  return (
    <AppCard
      title={title ?? `Đang ở bước ${station}`}
      meta={total ? `${total} lệnh` : undefined}
      flush
      className={fill ? "flex flex-col lg:min-h-0 lg:flex-1" : ""}
      bodyClassName={fill ? "flex flex-col lg:min-h-0 lg:flex-1" : ""}
    >
      {isError ? (
        <ErrorState error={error} onRetry={() => refetch()} />
      ) : isLoading ? (
        <EmptyState title="Đang tải…" />
      ) : !rows.length ? (
        <EmptyState
          icon={<Clock size={40} />}
          title="Không có lệnh nào trong tay trạm"
          hint="Quét nhận một lệnh ở hàng đợi phía trên."
        />
      ) : (
        <DataTable columns={columns} rows={body} fill={fill} maxHeight="30rem" pad="lg" />
      )}
      {hidden > 0 ? (
        <p className="border-t border-line px-4 py-3 text-body-sm text-fg-subtle sm:px-5">
          Còn {hidden} lệnh nữa chưa hiện — xử bớt việc ở trên rồi danh sách tự đẩy lên.
        </p>
      ) : null}
    </AppCard>
  );
}
