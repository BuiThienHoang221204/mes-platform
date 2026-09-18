"use client";

import { useState, type ReactNode } from "react";

import { AppButton } from "@/components/ui/AppButton";
import { AppCard } from "@/components/ui/AppCard";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import type { ApiError } from "@/types/api";

export type LegendKey = { color: string; label: string };

type Props = {
  title: ReactNode;
  meta?: ReactNode;
  controls?: ReactNode;
  legend?: LegendKey[];
  /** Bảng số — BẮT BUỘC có, không phải tiện ích. Xem chú thích dưới. */
  table?: ReactNode;
  isLoading?: boolean;
  error?: ApiError | Error | null;
  onRetry?: () => void;
  empty?: string;
  isEmpty?: boolean;
  /** Lấp hết chiều cao còn lại — biểu đồ tự lo phần nào bên trong sẽ cuộn. */
  fill?: boolean;
  children: ReactNode;
};

/**
 * Khung chung cho cả ba biểu đồ: tiêu đề, ô điều khiển, chú giải, và nút mở bảng số.
 *
 * `Xem dạng bảng` không phải tiện ích thêm thắt. Màu chỉ nói được thứ tự lớn nhỏ;
 * ai cần con số chính xác, cần copy đi chỗ khác, hay đang nhìn màn hình ngoài
 * xưởng bị chói thì bảng số là đường duy nhất. Nó cũng là phần đọc được bằng trình
 * đọc màn hình — mấy cái thanh `div` kia thì không.
 */
export function ChartFrame({
  title,
  meta,
  controls,
  legend,
  table,
  isLoading,
  error,
  onRetry,
  empty = "Chưa có số liệu trong khoảng này.",
  isEmpty,
  fill,
  children,
}: Props) {
  const [showTable, setShowTable] = useState(false);
  const scroll = Boolean(fill && showTable && table);

  return (
    <AppCard
      title={title}
      meta={meta}
      className={fill ? "flex flex-col lg:min-h-0 lg:flex-1" : ""}
      bodyClassName={
        fill ? `flex flex-col lg:min-h-0 lg:flex-1 ${scroll ? "lg:overflow-y-auto" : ""}` : ""
      }
      actions={
        <>
          {controls}
          {table ? (
            <AppButton
              size="md"
              className="shrink-0 text-body-sm"
              onClick={() => setShowTable((v) => !v)}
            >
              {showTable ? "Ẩn bảng" : "Xem dạng bảng"}
            </AppButton>
          ) : null}
        </>
      }
    >

      {legend?.length ? (
        <ul className="mb-4 flex shrink-0 flex-wrap gap-x-4 gap-y-2 text-body-sm text-fg-muted">
          {legend.map((k) => (
            <li key={k.label} className="flex items-center gap-2">
              <span className="h-3 w-3 rounded-xs" style={{ background: k.color }} aria-hidden />
              {k.label}
            </li>
          ))}
        </ul>
      ) : null}

      <div className={fill ? `flex flex-col ${scroll ? "lg:shrink-0" : "lg:min-h-0 lg:flex-1"}` : ""}>
        {error ? (
          <ErrorState error={error} onRetry={onRetry} />
        ) : isLoading ? (
          <p className="py-10 text-center text-body text-fg-subtle">Đang tải…</p>
        ) : isEmpty ? (
          <EmptyState title={empty} />
        ) : (
          children
        )}
      </div>

      {showTable && table ? (
        <div className="mt-5 shrink-0 border-t border-line pt-4">{table}</div>
      ) : null}
    </AppCard>
  );
}
