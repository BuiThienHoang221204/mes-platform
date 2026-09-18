"use client";

import { AppCard } from "@/components/ui/AppCard";
import { DataTable, type Column } from "@/components/ui/DataTable";
import { StatusPill } from "@/components/ui/StatusPill";
import { stationName } from "@/constants/stations";
import type { TraceRound } from "@/types/trace";
import { nfmt } from "@/utils/format";

const hhmm = (iso: string | null) => (iso ? iso.slice(11, 16) : "—");

const MUTED = "text-body-sm text-fg-muted";

const COLUMNS: Column[] = [
  { label: "Vòng" },
  { label: "Bắt đầu từ", cellClassName: MUTED },
  { label: "Nhập kho xong", cellClassName: `${MUTED} tnum` },
  { label: "SX đạt", right: true },
  { label: "SL hỏng", right: true },
  { label: "SL thiếu", right: true },
  { label: "Đã đóng thùng", right: true },
  { label: "Lý do hỏng", cellClassName: MUTED },
  { label: "Lý do thiếu", cellClassName: MUTED },
  { label: "Ghi chú đóng thùng", cellClassName: MUTED },
  { label: "Lý do trả lại", cellClassName: MUTED },
];

export function RoundTable({ rounds }: { rounds: TraceRound[] }) {
  const body = rounds.map((r) => {
    const p = r.production;
    const live = !r.closed_at;
    return {
      key: String(r.round_no),
      cells: [
        <span key="span" className="flex items-center gap-2">
          <span className="text-body-lg">Vòng {r.round_no}</span>
          {live ? (
            <StatusPill tone="accent" live>
              đang chạy
            </StatusPill>
          ) : null}
        </span>,
        `${r.started_from == null ? "Kho xuất" : stationName(r.started_from)} · ${hhmm(r.opened_at)}`,
        hhmm(r.packing?.completed_at ?? null),
        nfmt(p?.qty_ok),
        nfmt(p?.qty_ng),
        nfmt(p?.qty_short),
        nfmt(r.box_summary?.packed_pcs),
        p?.ng_reason_text ?? "—",
        p?.short_reason_text ?? "—",
        r.packing?.note_text ?? "—",
        live ? (
          <em className="text-fg-subtle">vòng chưa chốt sổ — số còn thay đổi</em>
        ) : (
          (r.return_reason_text ?? "—")
        ),
      ],
    };
  });

  return (
    <AppCard title="1 · Các vòng — kể cả vòng đang chạy" flush>
      <DataTable columns={COLUMNS} rows={body} nowrap />
      <div className="space-y-2 border-t border-line px-4 py-3 text-body-sm text-fg-muted">
        <p>
          <strong className="text-fg">Số về cột số, chữ về cột chữ.</strong> Bốn cột số đứng liền
          nhau để đọc lướt và cộng nhẩm được; ba cột lý do đứng liền nhau ở sau. Ba cột số đầu cộng
          lại đúng bằng mục tiêu vòng.
        </p>
        <p>
          <strong className="text-fg">Bắt đầu từ</strong> đọc thẳng nơi vòng đó mở, ghi lại ngay lúc
          mở vòng — không suy từ các bước đã đi. Suy thì vòng vừa mở luôn bị đoán nhầm thành Bàn
          team leader, kể cả khi QC vừa trả nó về Kho.
        </p>
      </div>
    </AppCard>
  );
}
