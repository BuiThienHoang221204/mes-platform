"use client";

import { BarRow } from "@/components/chart/BarRow";
import { DateRangePicker } from "@/components/ui/DateRangePicker";
import { Pager } from "@/components/ui/Pager";
import { ChartFrame } from "@/components/chart/ChartFrame";
import { ChartTable } from "@/components/chart/ChartTable";
import { useState } from "react";

import { useMoProgress } from "@/hooks/reports/useReports";
import { rangeOf, type DateRange } from "@/utils/dateRange";
import { nfmt } from "@/utils/format";

const DONE = "var(--color-series-1)";

/** ① Tiến độ theo lệnh — thanh có rãnh nền, mỗi lệnh một dòng.
 *
 *  Không dùng biểu đồ tròn: một tỷ lệ so với hạn mức thì thanh đọc nhanh hơn, và
 *  xếp nhiều dòng thì so được giữa các lệnh — việc mà mấy hình tròn cạnh nhau
 *  không làm nổi.
 */
const ROW_STEP_MS = 45;

export function MoProgress() {
  const [offset, setOffset] = useState(0);
  const [range, setRange] = useState<DateRange>(() => rangeOf("today") as DateRange);
  const { items: rows, total, limit, isLoading, error, refetch } = useMoProgress(
    { status: "PROCESSING", dateFrom: range.from, dateTo: range.to },
    offset,
  );

  const changeRange = (r: DateRange) => {
    setRange(r);
    setOffset(0);
  };

  return (
    <ChartFrame
      title="Tiến độ theo MO"
      meta="pcs đã nhập kho trên tổng số phải làm"
      controls={
        <div className="w-56 shrink-0">
          <DateRangePicker label="Ngày tạo lệnh" value={range} onChange={changeRange} />
        </div>
      }
      isLoading={isLoading}
      error={error}
      onRetry={() => void refetch()}
      isEmpty={!isLoading && rows.length === 0}
      empty={
        range.from || range.to
          ? "Không có lệnh nào đang chạy trong khoảng này."
          : "Không có lệnh nào đang chạy."
      }
      fill
      table={
        <ChartTable
          head={["Mã lệnh", "Con hàng", "Tổng SL", "Đã nhập kho", "Còn lại", "Hỏng", "Thiếu"]}
          numCols={[2, 3, 4, 5, 6]}
          rows={rows.map((m) => [
            m.code,
            m.product_name,
            nfmt(m.quantity),
            nfmt(m.qty_done),
            nfmt(m.qty_remain),
            nfmt(m.qty_ng_total),
            nfmt(m.qty_short_total),
          ])}
        />
      }
    >
      <div className="no-scrollbar min-h-0 flex-1 space-y-3 overflow-y-auto pr-1">
        {rows.map((m, i) => {
          const pct = m.quantity > 0 ? (m.qty_done / m.quantity) * 100 : 0;
          return (
            <BarRow
              key={m.code}
              delayMs={i * ROW_STEP_MS}
              label={m.code}
              sub={m.product_name}
              max={m.quantity || 1}
              title={`${m.code} · đã nhập kho ${nfmt(m.qty_done)}/${nfmt(m.quantity)} pcs`}
              segments={[{ value: m.qty_done, color: DONE, label: "Đã nhập kho" }]}
              value={
                <>
                  {nfmt(m.qty_done)}
                  <span className="text-fg-subtle"> / {nfmt(m.quantity)}</span>
                  <span className="ml-2">{Math.round(pct)}%</span>
                </>
              }
            />
          );
        })}
      </div>

      <Pager
        offset={offset}
        shown={rows.length}
        total={total}
        limit={limit}
        onOffset={setOffset}
        unit="lệnh"
        className="mt-4 border-t-0 px-0 pb-0 pt-4"
      />
    </ChartFrame>
  );
}
