"use client";

import { useQueryClient } from "@tanstack/react-query";

import { AppButton } from "@/components/ui/AppButton";
import { AppCard } from "@/components/ui/AppCard";
import { DataTable, type Column } from "@/components/ui/DataTable";
import { EmptyState } from "@/components/ui/EmptyState";
import { StatusPill } from "@/components/ui/StatusPill";
import { actionMeta } from "@/constants/actionNames";
import { moKeys } from "@/constants/queryKeys";
import { STEP_NAME } from "@/constants/stepNames";
import { EVENT_PAGE, useEvents } from "@/hooks/production/useProduction";
import type { TraceEvent } from "@/types/trace";

type Props = { code: string; first: TraceEvent[]; total: number };

const MUTED = "text-body-sm text-fg-muted";

const COLUMNS: Column[] = [
  { label: "Ngày", cellClassName: `${MUTED} tnum` },
  { label: "Giờ", cellClassName: `${MUTED} tnum` },
  { label: "Bước", cellClassName: "text-body-sm" },
  { label: "Hành động" },
  { label: "Chuyển trạng thái", cellClassName: MUTED },
  { label: "Lý do", cellClassName: `${MUTED} whitespace-normal` },
];

export function EventLogTable({ code, first, total }: Props) {
  const qc = useQueryClient();
  const { data, fetchNextPage, hasNextPage, isFetchingNextPage } = useEvents(code, first, total);

  const pages = data?.pages ?? [];
  const rows = pages.flatMap((p) => p.items);

  const collapse = () =>
    qc.setQueryData(moKeys.events(code), (old: typeof data) =>
      old ? { pages: old.pages.slice(0, 1), pageParams: old.pageParams.slice(0, 1) } : old,
    );

  const body = rows.map((e, i) => {
    const act = actionMeta(e.action);
    return {
      key: `${e.at}-${i}`,
      cells: [
        e.at.slice(0, 10),
        e.at.slice(11, 16),
        e.step_no == null ? "—" : `${e.step_no} · ${STEP_NAME[e.step_no] ?? ""}`,
        <span key="span" title={e.action}>
          <StatusPill tone={act.tone}>{act.label}</StatusPill>
        </span>,
        e.from || e.to ? `${e.from || "—"} → ${e.to || "—"}` : "—",
        e.reason ?? "—",
      ],
    };
  });

  return (
    <AppCard title="3 · Nhật ký đầy đủ" meta={`${rows.length}/${total} bản ghi · chỉ ghi thêm`} flush>
      {!rows.length ? (
        <EmptyState title="Chưa có bản ghi nào" />
      ) : (
        <DataTable columns={COLUMNS} rows={body} nowrap />
      )}
      {rows.length ? (
        <div className="flex flex-wrap items-center gap-3 border-t border-line px-4 py-3">
          {hasNextPage ? (
            <AppButton size="sm" disabled={isFetchingNextPage} onClick={() => fetchNextPage()}>
              {isFetchingNextPage
                ? "Đang tải…"
                : `Xem thêm ${Math.min(EVENT_PAGE, total - rows.length)} dòng`}
            </AppButton>
          ) : null}
          {pages.length > 1 ? (
            <AppButton size="sm" variant="ghost" onClick={collapse}>
              Thu gọn
            </AppButton>
          ) : null}
          <span className="text-body-sm text-fg-subtle">
            {hasNextPage ? `còn ${total - rows.length} dòng cũ hơn` : "đã hiện hết"}
          </span>
        </div>
      ) : null}

      <p className="border-t border-line px-4 py-3 text-body-sm text-fg-muted">
        Nhật ký chỉ thêm, không sửa không xoá, giữ vĩnh viễn. Mỗi hành động ghi lệnh, vòng, bước,
        người làm, thời điểm, chuyển trạng thái và lý do. Rê chuột lên tên hành động để xem mã gốc
        khi cần đối chiếu với log máy chủ.
      </p>
    </AppCard>
  );
}
