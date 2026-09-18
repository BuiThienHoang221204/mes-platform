"use client";

import { Package } from "@/components/common/PhosphorIcons";
import { AppCard } from "@/components/ui/AppCard";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { RoundBadge } from "@/components/ui/RoundBadge";
import { waitingSince } from "@/constants/flow";
import { useQueue } from "@/hooks/board/useBoard";
import { useScanStore } from "@/stores/useScanStore";
import { boxLabel, dur, nfmt } from "@/utils/format";

type Props = {
  station: number;
  title?: string;
  /** Mặc định lấp hết chiều cao còn lại. Tắt thì dùng trần cứng `30rem`. */
  fill?: boolean;
  actions?: React.ReactNode;
};

export function QueueList({ station, title = "Hàng đợi", fill = true, actions }: Props) {
  const { items: rows, total, isLoading, isError, error, refetch } = useQueue(station);
  const setDraft = useScanStore((s) => s.setDraft);

  const hidden = total - rows.length;

  return (
    <AppCard
      title={title}
      meta={total ? `${total} lệnh` : undefined}
      actions={actions}
      flush
      className={fill ? "flex flex-col lg:min-h-0 lg:flex-1" : ""}
      bodyClassName={fill ? "flex flex-col lg:min-h-0 lg:flex-1" : ""}
    >
      {isError ? (
        <ErrorState error={error} onRetry={() => refetch()} />
      ) : isLoading ? (
        <EmptyState title="Đang tải hàng đợi…" />
      ) : !rows.length ? (
        <EmptyState
          icon={<Package size={40} />}
          title="Hàng đợi trống"
          hint="Chưa có lệnh nào chờ ở trạm này."
        />
      ) : (
        <div
          className={
            fill ? "overflow-auto lg:min-h-0 lg:flex-1" : "max-h-[30rem] overflow-auto"
          }
        >
          <ul className="w-max min-w-full sm:w-auto">
            {rows.map((r) => (
              <li key={r.code} className="border-b border-line last:border-b-0">
                <button
                  type="button"
                  onClick={() => setDraft(r.code)}
                  className="flex min-h-touch w-full flex-nowrap items-center gap-x-3 gap-y-2 px-4 py-3 text-left hover:bg-surface-2 sm:flex-wrap sm:gap-x-4 sm:px-5"
                >
                  <span className="w-28 shrink-0 font-mono text-body-lg text-fg">{r.code}</span>

                  <span className="min-w-0 flex-1">
                    <span className="block truncate text-body text-fg">{r.product_name}</span>
                    <span className="block truncate text-caption text-fg-subtle">
                      {waitingSince(station)} · {dur(r.waiting_sec)}
                    </span>
                  </span>

                  <span className="w-40 shrink-0 sm:w-auto">
                    <RoundBadge round={r.round_no} target={r.target_qty} quantity={r.quantity} />
                  </span>

                  <span className="w-28 shrink-0 text-right">
                    {station === 5 ? (
                      <>
                        <span className="block text-body tnum text-fg">
                          {boxLabel(r.qty_packed ?? 0, r.pcs_per_box ?? 0)}
                        </span>
                        <span className="block text-caption tnum text-fg-subtle">
                          {nfmt(r.qty_packed ?? 0)} pcs
                        </span>
                      </>
                    ) : (
                      <>
                        <span className="block text-body tnum text-fg">
                          {nfmt(r.target_qty ?? r.quantity)}
                        </span>
                        <span className="block text-caption text-fg-subtle">
                          {r.target_qty && r.target_qty < r.quantity ? "còn lại" : "pcs"}
                        </span>
                      </>
                    )}
                  </span>
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}
      {hidden > 0 ? (
        <p className="border-t border-line px-4 py-3 text-body-sm text-fg-subtle sm:px-5">
          Còn {hidden} lệnh nữa chưa hiện — xử bớt việc ở trên rồi danh sách tự đẩy lên.
        </p>
      ) : null}
    </AppCard>
  );
}
