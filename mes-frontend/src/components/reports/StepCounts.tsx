"use client";

import { useState } from "react";

import { ChartFrame } from "@/components/chart/ChartFrame";
import { ChartTable } from "@/components/chart/ChartTable";
import { ColumnChart } from "@/components/chart/ColumnChart";
import { DateRangePicker } from "@/components/ui/DateRangePicker";
import { STATIONS } from "@/constants/stations";
import { useCounts } from "@/hooks/board/useBoard";
import { rangeOf, type DateRange } from "@/utils/dateRange";

const WAIT = "var(--color-series-2)";
const HOLD = "var(--color-series-1)";

/** MO theo giai đoạn — sáu trạm, tách CHỜ NHẬN và ĐANG LÀM.
 *
 *  Gộp hai số lại thì mất đúng thứ người điều độ cần: việc cần người đi quét khác
 *  hẳn việc đang chạy. Trạm có 5 lệnh chờ là trạm đang tắc; trạm có 5 lệnh đang
 *  làm là trạm đang chạy hết công suất.
 */
export function StepCounts() {
  const [range, setRange] = useState<DateRange>(() => rangeOf("today") as DateRange);
  const { data, isLoading, error, refetch } = useCounts(range);

  const rows = STATIONS.map((s) => {
    const k = String(s.no);
    return {
      ...s,
      wait: data?.counts?.[k] ?? 0,
      hold: data?.holding?.[k] ?? 0,
    };
  });
  const max = Math.max(...rows.flatMap((r) => [r.wait, r.hold]), 1);

  return (
    <ChartFrame
      title="MO theo giai đoạn"
      meta="giữ đúng thứ tự quy trình 0 → 5"
      controls={
        <div className="w-56 shrink-0">
          <DateRangePicker label="Ngày tạo lệnh" value={range} onChange={setRange} />
        </div>
      }
      legend={[
        { color: WAIT, label: "Chờ nhận" },
        { color: HOLD, label: "Đang làm" },
      ]}
      isLoading={isLoading}
      error={error}
      onRetry={() => void refetch()}
      isEmpty={!isLoading && !data}
      fill
      table={
        <ChartTable
          head={["Bước", "Tên trạm", "Chờ nhận", "Đang làm", "Tổng"]}
          numCols={[2, 3, 4]}
          rows={rows.map((r) => [r.no, r.name, r.wait, r.hold, r.wait + r.hold])}
        />
      }
    >
      <ColumnChart
        height={260}
        max={max}
        columns={rows.map((r) => ({
          key: String(r.no),
          label: r.name,
          sub: `bước ${r.no}`,
          title: `${r.name} — chờ nhận ${r.wait}, đang làm ${r.hold}`,
          segments: [
            { value: r.wait, color: WAIT, label: "Chờ nhận" },
            { value: r.hold, color: HOLD, label: "Đang làm" },
          ],
        }))}
      />
    </ChartFrame>
  );
}
