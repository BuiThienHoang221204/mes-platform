"use client";

import Link from "next/link";
import { useState } from "react";

import { AppButton } from "@/components/ui/AppButton";
import { AppCard } from "@/components/ui/AppCard";
import { CheckSquare } from "@/components/common/PhosphorIcons";
import { AppDropdown, type DropdownOption } from "@/components/ui/AppDropdown";
import { DataTable, type Column } from "@/components/ui/DataTable";
import { DateRangePicker } from "@/components/ui/DateRangePicker";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { Pager } from "@/components/ui/Pager";
import { MoStatusPill, StatusPill } from "@/components/ui/StatusPill";
import { MO_FILTERS, MO_STATUS, MO_STATUS_LABEL } from "@/constants/status";
import { useRunning } from "@/hooks/board/useBoard";
import { useMoActions, useMoList } from "@/hooks/mo/useMo";
import type { MoStatus } from "@/types/mo";
import { rangeOf, type DateRange } from "@/utils/dateRange";
import { dur, nfmt } from "@/utils/format";

const ALL = "all";

const STATUS_OPTIONS: DropdownOption[] = [
  { value: ALL, label: "Tất cả" },
  ...MO_FILTERS.map((s) => ({ value: s, label: MO_STATUS_LABEL[s] })),
];

const COLUMNS: Column[] = [
  { label: "Mã lệnh" },
  { label: "Tên con hàng" },
  { label: "Số lượng", right: true },
  { label: "Quy cách", right: true },
  { label: "TG yêu cầu", cellClassName: "text-body-sm tnum text-fg-muted" },
  { label: "Trạng thái" },
  { label: "Vòng", right: true },
  { label: "Ghi chú" },
  { label: "", right: true },
];

type Props = {
  status?: MoStatus;
  onStatus?: (s: MoStatus | null) => void;
};

export function MoTable({ status, onStatus }: Props) {
  const [offset, setOffset] = useState(0);
  const [range, setRange] = useState<DateRange>(() => rangeOf("today") as DateRange);
  const { items: rows, total, limit, isError, error, refetch, isLoading } =
    useMoList({ status, dateFrom: range.from, dateTo: range.to }, offset);

  const goPage = (n: number) => {
    setOffset(n);
    setPicked([]);
  };

  const togglePicking = () => {
    setPicked([]);
    setPicking((v) => !v);
  };

  const changeRange = (r: DateRange) => {
    setRange(r);
    goPage(0);
  };
  const isFiltered = Boolean(range.from || range.to);
  const { items: running } = useRunning(0, 100);
  const { submit, cancel, submitBatch, cancelBatch } = useMoActions();
  const [picking, setPicking] = useState(false);
  const [picked, setPicked] = useState<string[]>([]);

  const roundOf = (code: string) => running.find((r) => r.code === code);

  const canSubmit = (st: MoStatus) => st === MO_STATUS.DRAFT;
  const canCancel = (st: MoStatus) => st === MO_STATUS.DRAFT || st === MO_STATUS.SUBMITTED;

  const onPage = new Map(rows.map((m) => [m.code, m.status as MoStatus]));
  const pickedHere = picked.filter((c) => onPage.has(c));
  const submitable = pickedHere.filter((c) => canSubmit(onPage.get(c) as MoStatus));
  const cancellable = pickedHere.filter((c) => canCancel(onPage.get(c) as MoStatus));
  const busy = submitBatch.isPending || cancelBatch.isPending;

  const askCancel = (codes: string[]) => {
    const reason = window.prompt(`Lý do huỷ ${codes.length} lệnh?`);
    if (reason?.trim()) {
      cancelBatch.mutate(
        { codes, reason: reason.trim() },
        { onSuccess: () => setPicked([]) },
      );
    }
  };

  if (isError) return <ErrorState error={error} onRetry={() => refetch()} />;

  const body = rows.map((m) => {
    const run = roundOf(m.code);
    const done = run ? m.quantity - run.target_qty : 0;
    return {
      key: m.code,
      selectable: canSubmit(m.status) || canCancel(m.status),
      cells: [
        <Link key="link" href={`/mos/${m.code}/trace`} className="font-mono text-body-lg text-accent">
          {m.code}
        </Link>,
        m.product_name,
        nfmt(m.quantity),
        m.pcs_per_box || "—",
        dur(m.required_production_sec),
        <MoStatusPill key="mostatuspill" status={m.status} />,
        run?.round_no ?? "—",
        <span key="span" className="flex flex-wrap gap-1.5">
          {run && run.round_no > 1 ? <StatusPill tone="warn">Vòng {run.round_no}</StatusPill> : null}
          {run && done > 0 ? (
            <StatusPill tone="flat">
              Đã xong {nfmt(done)} · Còn {nfmt(run.target_qty)}
            </StatusPill>
          ) : null}
          {m.pcs_per_box === 0 ? <StatusPill tone="flat">Không đóng thùng</StatusPill> : null}
          {run?.on_time === false ? <StatusPill tone="danger">Quá giờ</StatusPill> : null}
        </span>,
        <div key="div" className="flex justify-end gap-2">
          {m.status === MO_STATUS.DRAFT ? (
            <AppButton
              size="sm"
              variant="primary"
              disabled={submit.isPending}
              onClick={() => submit.mutate(m.code)}
            >
              Chốt lệnh
            </AppButton>
          ) : null}
          {m.status === MO_STATUS.DRAFT || m.status === MO_STATUS.SUBMITTED ? (
            <AppButton
              size="sm"
              variant="danger"
              disabled={cancel.isPending}
              onClick={() => {
                const reason = window.prompt("Lý do huỷ lệnh?");
                if (reason?.trim()) cancel.mutate({ code: m.code, reason: reason.trim() });
              }}
            >
              Huỷ
            </AppButton>
          ) : null}
        </div>,
      ],
    };
  });

  return (
    <AppCard
      title="Sổ lệnh"
      meta={total ? `${offset + 1}–${offset + rows.length} trên ${total} lệnh` : undefined}
      actions={
        <div className="flex w-full flex-wrap items-center gap-2 sm:w-auto sm:gap-3">
          <AppButton
            size="md"
            variant={picking ? "primary" : "outline"}
            icon={<CheckSquare size={20} />}
            onClick={togglePicking}
          >
            {picking ? "Thoát chọn" : "Chọn nhiều"}
          </AppButton>
          {onStatus ? (
            <AppDropdown
              label="Trạng thái"
              value={status ?? ALL}
              options={STATUS_OPTIONS}
              onChange={(v) => {
                onStatus(v === ALL ? null : (v as MoStatus));
                goPage(0);
              }}
              className="min-w-0 flex-1 sm:w-48 sm:flex-none"
            />
          ) : null}
          <div className="w-full shrink-0 sm:w-64">
            <DateRangePicker label="Ngày tạo lệnh" value={range} onChange={changeRange} />
          </div>
        </div>
      }
      flush
    >
      {isLoading ? (
        <EmptyState title="Đang tải…" />
      ) : !rows.length ? (
        <EmptyState
          title={isFiltered ? "Không có lệnh nào trong khoảng này" : "Chưa có lệnh nào"}
          hint={isFiltered ? "Nới khoảng ngày hoặc bỏ lọc." : "Tạo lệnh mới hoặc nhập từ tệp Excel."}
        />
      ) : (
        <>
          {picking && pickedHere.length ? (
            <div className="flex flex-wrap items-center gap-2 border-b border-line bg-accent-soft px-4 py-3 sm:gap-3 sm:px-5">
              <span className="text-body text-accent">
                Đã chọn {pickedHere.length} lệnh
              </span>
              <AppButton
                size="sm"
                variant="primary"
                disabled={!submitable.length || busy}
                onClick={() =>
                  submitBatch.mutate(submitable, { onSuccess: () => setPicked([]) })
                }
              >
                Chốt {submitable.length} lệnh
              </AppButton>
              <AppButton
                size="sm"
                variant="danger"
                disabled={!cancellable.length || busy}
                onClick={() => askCancel(cancellable)}
              >
                Huỷ {cancellable.length} lệnh
              </AppButton>
              <AppButton size="sm" variant="ghost" onClick={() => setPicked([])}>
                Bỏ chọn
              </AppButton>
            </div>
          ) : null}
          <DataTable
            columns={COLUMNS}
            rows={body}
            nowrap
            selection={picking ? { picked, onPick: setPicked } : undefined}
          />
        </>
      )}

      <Pager offset={offset} shown={rows.length} total={total} limit={limit} onOffset={goPage} />
    </AppCard>
  );
}
