"use client";

import { useMemo, useState } from "react";

import { BarRow } from "@/components/chart/BarRow";
import { ChartFrame } from "@/components/chart/ChartFrame";
import { ChartTable } from "@/components/chart/ChartTable";
import { AppDate } from "@/components/ui/AppDate";
import { AppDropdown } from "@/components/ui/AppDropdown";
import { Note } from "@/components/ui/Note";
import { useHourly } from "@/hooks/reports/useReports";
import { nfmt, today } from "@/utils/format";
import {
  addDays,
  bySlot,
  dayOf,
  slotRange,
  TIER_COLOR,
  tierLegend,
  tierOf,
  type SlotRow,
} from "@/utils/reports";

/** Trần cắt dòng. KHÔNG được giấu lệnh hụt — xem `cap` bên dưới. */
const TOP_CAP = 25;

const pct = (n: number) => `${n.toLocaleString("vi-VN", { maximumFractionDigits: 1 })}%`;

/**
 * ② Đạt định mức theo giờ — MỘT khung giờ, TẤT CẢ lệnh, tệ nhất lên đầu.
 *
 * Thời gian là BỘ LỌC chứ không nằm trên trục. Ép cả hai chiều (giờ × lệnh) vào
 * một hình thì vỡ ngay ở 8 lệnh: mỗi cột còn 2,5px. Bỏ một chiều ra thì cột làm
 * đúng việc nó giỏi nhất — xếp hạng — và chịu được 100 lệnh mà không thêm màu nào.
 *
 * Chiều thời gian mất đi được trả lại bằng MŨI TÊN chênh so với khung trước: hụt
 * lần đầu khác hẳn hụt lần thứ tư liên tiếp. Vì thế cửa sổ tải là HAI ngày —
 * khung đầu ngày phải so được với khung cuối ngày hôm trước, không thì mỗi sáng
 * mũi tên trống trơn.
 */
const ROW_STEP_MS = 45;

export function SlotRanking() {
  const [day, setDay] = useState(today);
  const [bucket, setBucket] = useState(1);
  const [slot, setSlot] = useState<string>("");

  const { data, isLoading, error, refetch } = useHourly({
    bucket,
    dateFrom: addDays(day, -1),
    dateTo: day,
  });

  const { keys, slots, ends } = useMemo(() => bySlot(data), [data]);
  const inDay = useMemo(() => keys.filter((k) => dayOf(k) === day), [keys, day]);

  const targetPct = data?.target_pct ?? 85;
  const span = data ? data.shift.shift_end - data.shift.shift_start : 9;

  const chosen = inDay.includes(slot) ? slot : (inDay[inDay.length - 1] ?? "");
  const rows = slots.get(chosen) ?? [];
  const prevRates = useMemo(() => {
    const i = keys.indexOf(chosen);
    const before = i > 0 ? (slots.get(keys[i - 1]) ?? []) : [];
    return new Map(before.map((r) => [r.code, r.rate]));
  }, [keys, chosen, slots]);

  const short = rows.filter((r) => r.rate < targetPct);
  const qty = rows.reduce((n, r) => n + r.qty, 0);
  const target = rows.reduce((n, r) => n + r.target, 0);
  const heroRate = target > 0 ? (qty / target) * 100 : 0;

  const cap = Math.max(TOP_CAP, short.length);
  const shown = rows.slice(0, cap);
  const max = Math.max(...rows.map((r) => r.rate), 100) * 1.06;

  const delta = (r: SlotRow) => {
    const before = prevRates.get(r.code);
    if (before == null) return null;
    const d = r.rate - before;
    return `${d >= 0 ? "▲" : "▼"}${Math.abs(d).toLocaleString("vi-VN", { maximumFractionDigits: 1 })}`;
  };

  return (
    <ChartFrame
      title="Tiến độ theo giờ"
      meta={
        rows.length
          ? `một khung giờ · tất cả lệnh · tệ nhất lên đầu · ${short.length}/${rows.length} lệnh dưới mục tiêu`
          : undefined
      }
      legend={tierLegend(targetPct)}
      controls={
        <div className="flex flex-wrap items-center gap-2">
          <AppDate
            label="Ngày xem"
            className="w-36 shrink-0"
            value={day}
            max={today()}
            onChange={(v) => {
              setDay(v || today());
              setSlot("");
            }}
          />
          <AppDropdown
            label="Khung gộp"
            className="w-32 shrink-0"
            value={String(bucket)}
            onChange={(v) => {
              setBucket(Number(v));
              setSlot("");
            }}
            options={[
              { value: "1", label: "1 giờ" },
              { value: "4", label: "4 giờ" },
              { value: String(span), label: `${span} giờ · cả ca` },
            ]}
          />
          <AppDropdown
            label="Khung giờ"
            className="w-40 shrink-0"
            value={chosen}
            onChange={setSlot}
            options={inDay.map((k) => ({ value: k, label: slotRange(k, ends.get(k)) }))}
            placeholder={inDay.length ? "Chọn khung giờ" : "Chưa có khung nào"}
          />
        </div>
      }
      isLoading={isLoading}
      error={error}
      onRetry={() => void refetch()}
      isEmpty={!isLoading && inDay.length === 0}
      empty="Ngày này chưa có khung giờ nào ghi sổ."
      fill
      table={
        <ChartTable
          head={["Lệnh", "Yêu cầu", "Thực tế", "Số người", "Đạt %", "So mục tiêu"]}
          numCols={[1, 2, 3, 4]}
          rows={rows.map((r) => [
            r.code,
            nfmt(r.target),
            nfmt(r.qty),
            nfmt(r.headcount),
            pct(r.rate),
            r.rate >= targetPct ? "Đạt" : `Thiếu ${pct(targetPct - r.rate)} điểm`,
          ])}
        />
      }
    >
      <div className="mb-4 flex shrink-0 flex-wrap items-baseline gap-4">
        <span
          className={`text-display tnum ${heroRate < targetPct ? "text-tier-low" : "text-fg"}`}
        >
          {target > 0 ? pct(heroRate) : "—"}
        </span>
        <span className="text-body-sm text-fg-muted">
          {slotRange(chosen, ends.get(chosen))} — {rows.length} lệnh chạy,{" "}
          {short.length ? `${short.length} lệnh hụt` : "không lệnh nào hụt"} · làm được{" "}
          {nfmt(qty)} trên định mức {nfmt(target)} cái
        </span>
      </div>

      <div className="no-scrollbar min-h-0 flex-1 space-y-2 overflow-y-auto pr-1">
        {shown.map((r, i) => {
          const d = delta(r);
          return (
            <BarRow
              key={r.code}
              delayMs={i * ROW_STEP_MS}
              label={r.code}
              max={max}
              title={`${r.code} · ${nfmt(r.qty)}/${nfmt(r.target)} cái`}
              segments={[
                { value: Math.min(r.rate, max), color: TIER_COLOR[tierOf(r.rate, targetPct)], label: "Đạt" },
              ]}
              marks={[
                { at: targetPct, label: `mục tiêu ${targetPct}%` },
                { at: 100, label: "đủ định mức 100%", faint: true },
              ]}
              value={
                <>
                  {pct(r.rate)}
                  {d ? <span className="ml-2 text-caption text-fg-subtle">{d}</span> : null}
                </>
              }
            />
          );
        })}
      </div>

      {rows.length > cap ? (
        <p className="mt-3 text-body-sm text-fg-subtle">
          Còn {rows.length - cap} lệnh nữa, tất cả đều đạt mục tiêu.
        </p>
      ) : null}

      <div className="mt-4 space-y-2">
        {data?.skipped_rows ? (
          <Note tone="warn">
            Đã bỏ <b>{data.skipped_rows} dòng</b> chưa khai sản lượng yêu cầu — không có mẫu
            số thì không tính được đạt bao nhiêu phần trăm.
          </Note>
        ) : null}
        {data?.folded_rows ? (
          <Note tone="warn">
            <b>{data.folded_rows} dòng</b> ghi ngoài giờ đi làm (tăng ca, hoặc trưa không
            nghỉ) đã gộp vào khung gần nhất — tổng vẫn đúng, nhưng nhãn khung không nói hết.
            Xem khung <b>1 giờ</b> để thấy đúng giờ của chúng.
          </Note>
        ) : null}
      </div>
    </ChartFrame>
  );
}
