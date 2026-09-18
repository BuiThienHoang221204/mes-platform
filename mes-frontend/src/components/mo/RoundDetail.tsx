"use client";

import { useEffect, useState } from "react";

import { AppButton } from "@/components/ui/AppButton";
import { AppCard } from "@/components/ui/AppCard";
import { DataTable, type Column } from "@/components/ui/DataTable";
import { EmptyState } from "@/components/ui/EmptyState";
import { productionService } from "@/services/production.service";
import type { TraceBoxHourly, TraceHourly, TraceRound } from "@/types/trace";
import { dur, nfmt, slotLabel } from "@/utils/format";
import { boxBreakdown, reconcileBoxes } from "@/utils/packing";
import { hourlyTotal } from "@/utils/trace";

const MUTED = "tnum text-fg-muted";

const LINE_COLS: Column[] = [
  { label: "Chuyền", cellClassName: "font-mono text-body-lg" },
  { label: "Thời gian chờ", cellClassName: MUTED },
  { label: "Thời gian chạy", cellClassName: "tnum" },
  { label: "Hạn mức vòng", cellClassName: MUTED },
];

const HOUR_COLS: Column[] = [
  { label: "Ngày", cellClassName: `text-body-sm ${MUTED}` },
  { label: "Khung giờ", cellClassName: "tnum" },
  { label: "Số người", right: true },
  { label: "Yêu cầu", right: true },
  { label: "Thực tế", right: true },
  { label: "Đạt", right: true },
  { label: "Năng suất", right: true },
];

const BOX_COLS: Column[] = [
  { label: "Ngày", cellClassName: `text-body-sm ${MUTED}` },
  { label: "Khung giờ", cellClassName: "tnum" },
  { label: "Số thùng", right: true },
  { label: "Quy cách", right: true, cellClassName: "text-fg-muted" },
  { label: "Thành pcs", right: true },
  { label: "Cộng dồn", right: true, cellClassName: "text-fg-muted" },
];

function Reconcile({ round }: { round: TraceRound }) {
  const sum = hourlyTotal(round);
  const ok = round.production?.qty_ok;
  if (ok == null) {
    return <span className="text-fg-muted">Σ giờ {nfmt(sum)} — chưa chốt sổ sản xuất</span>;
  }
  if (sum === ok) return <span className="text-ok">Σ giờ {nfmt(sum)} — khớp số đã chốt</span>;
  if (sum < ok) {
    return (
      <span className="text-fg-muted">
        Σ giờ {nfmt(sum)} &lt; đạt {nfmt(ok)} — ghi sót giờ, bình thường
      </span>
    );
  }
  return (
    <span className="text-danger">
      Σ giờ {nfmt(sum)} &gt; đạt {nfmt(ok)} — bất thường, ghi trùng hoặc khai thiếu
    </span>
  );
}

/**
 * Đối soát sổ thùng — dùng chung cách gọi tên với màn Sản xuất.
 *
 * Trước đây ô này gọi cả phần chênh là "Thùng lẻ · chưa đủ thùng". Sai: với quy
 * cách 400, chênh 2.100 là 5 THÙNG ĐẦY chưa ai ghi sổ cộng 100 lẻ. Một cái là
 * việc còn phải làm, một cái là bình thường — gộp lại thì con số duy nhất có thể
 * bắt được sổ ghi sót lại mang nhãn "không sao đâu".
 */
function BoxReconcile({ round, pcsPerBox }: { round: TraceRound; pcsPerBox: number }) {
  const box = reconcileBoxes(round, pcsPerBox);
  if (box.matched)
    return <span className="text-ok">Σ thùng {nfmt(box.packedPcs)} pcs — khớp số làm ra</span>;
  if (box.unloggedBoxes)
    return (
      <span className="text-warn">
        Σ thùng {nfmt(box.packedPcs)} pcs — sổ giờ chạy sau thực tế {box.unloggedBoxes} thùng
        {box.loosePcs ? ` (còn ${nfmt(box.loosePcs)} pcs chưa đủ một thùng)` : ""}
      </span>
    );
  return (
    <span className="text-fg-muted">
      Σ thùng {nfmt(box.packedPcs)} pcs — còn {nfmt(box.loosePcs)} pcs chưa đủ một thùng, vào
      thùng lẻ cuối lúc chốt
    </span>
  );
}

/**
 * Nạp tiếp một sổ đã bị cắt trang trong cây truy cứu.
 *
 * Trả về mảng ĐÃ GHÉP, luôn là phần đầu liên tục của sổ — cột cộng dồn trong bảng
 * thùng dựa vào đúng tính chất đó, ghép lộn xộn là con số cộng dồn sai.
 */
function useMoreRows<T>(
  first: T[],
  total: number,
  fetchPage: (offset: number) => Promise<{ items: T[] }>,
) {
  const [extra, setExtra] = useState<T[]>([]);
  const [isLoading, setDangTai] = useState(false);

  useEffect(() => setExtra([]), [first]);

  const rows = [...first, ...extra];
  const loadMore = async () => {
    setDangTai(true);
    try {
      const p = await fetchPage(rows.length);
      setExtra((cu) => [...cu, ...p.items]);
    } finally {
      setDangTai(false);
    }
  };
  return { rows, remaining: total - rows.length, loadMore, isLoading };
}

function MoreBar({
  remaining,
  isLoading,
  onMore,
}: {
  remaining: number;
  isLoading: boolean;
  onMore: () => void;
}) {
  if (remaining <= 0) return null;
  return (
    <div className="flex items-center gap-3 border-t border-line px-5 py-3">
      <AppButton size="md" disabled={isLoading} onClick={onMore}>
        {isLoading ? "Đang tải…" : "Xem thêm"}
      </AppButton>
      <span className="text-body-sm tnum text-fg-subtle">còn {remaining} dòng nữa</span>
    </div>
  );
}

export function RoundDetail({
  code,
  round,
  pcsPerBox,
}: {
  code: string;
  round: TraceRound;
  pcsPerBox: number;
}) {
  const hourly = useMoreRows<TraceHourly>(round.hourly, round.hourly_total, (offset) =>
    productionService.roundHourly(code, round.round_no, offset),
  );
  const boxes = useMoreRows<TraceBoxHourly>(
    round.packing_hourly,
    round.packing_hourly_total,
    (offset) => productionService.roundBoxes(code, round.round_no, offset),
  );

  return (
    <div className="space-y-5">
      <AppCard title={`Vòng ${round.round_no} · năng suất từng chuyền`} flush>
        {!round.lines.length ? (
          <EmptyState title="Vòng này chưa gán chuyền nào" />
        ) : (
          <DataTable
            columns={LINE_COLS}
            rows={round.lines.map((l) => ({
              key: l.line_code,
              cells: [l.line_code, dur(l.wait_sec), dur(l.run_sec), dur(round.required_sec)],
            }))}
            pad="lg"
          />
        )}
      </AppCard>

      <AppCard title={`Vòng ${round.round_no} · sản lượng theo giờ`} flush>
        {!hourly.rows.length ? (
          <EmptyState title="Vòng này chưa ghi giờ nào" />
        ) : (
          <DataTable
            columns={HOUR_COLS}
            rows={hourly.rows.map((h) => {
              const rate = h.target_qty ? Math.round((h.qty / h.target_qty) * 100) : null;
              const per = h.headcount ? (h.qty / h.headcount).toFixed(1) : null;
              return {
                key: `${h.work_date}-${h.slot_hour}`,
                cells: [
                  h.work_date,
                  slotLabel(h.slot_hour),
                  nfmt(h.headcount),
                  nfmt(h.target_qty),
                  nfmt(h.qty),
                  rate == null ? "—" : `${rate}%`,
                  per ?? "—",
                ],
              };
            })}
            pad="lg"
          />
        )}
        <MoreBar remaining={hourly.remaining} isLoading={hourly.isLoading} onMore={hourly.loadMore} />
        <p className="border-t border-line px-5 py-3 text-body-sm">
          <Reconcile round={round} />
        </p>
      </AppCard>

      <AppCard title={`Vòng ${round.round_no} · đóng thùng`} flush>
        {!boxes.rows.length ? (
          <EmptyState title="Vòng này chưa ghi thùng nào" />
        ) : (
          <DataTable
            columns={BOX_COLS}
            rows={boxes.rows.map((b, i) => ({
              key: `${b.work_date}-${b.slot_hour}`,
              cells: [
                b.work_date,
                slotLabel(b.slot_hour),
                nfmt(b.boxes),
                nfmt(b.pcs_per_box),
                nfmt(b.boxes * b.pcs_per_box),
                nfmt(
                  boxes.rows.slice(0, i + 1).reduce((n, x) => n + x.boxes * x.pcs_per_box, 0),
                ),
              ],
            }))}
            pad="lg"
          />
        )}
        <MoreBar remaining={boxes.remaining} isLoading={boxes.isLoading} onMore={boxes.loadMore} />
        <div className="space-y-1 border-t border-line px-5 py-3 text-body-sm">
          <p>
            <BoxReconcile round={round} pcsPerBox={pcsPerBox} />
          </p>
          {round.packing?.completed_at ? (
            <p className="text-fg-muted">
              Đã chốt {nfmt(round.packing.qty_packed ?? 0)} pcs
              {pcsPerBox > 0
                ? (() => {
                    const p = boxBreakdown(round.packing.qty_packed ?? 0, pcsPerBox);
                    return ` = ${p.full} thùng đầy${p.last ? ` + 1 thùng lẻ ${nfmt(p.last)}` : ""}`;
                  })()
                : ""}
              . Thùng cuối đóng thiếu là mặc định, không phải ngoại lệ.
            </p>
          ) : null}
        </div>
      </AppCard>
    </div>
  );
}
