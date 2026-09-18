import type { Trace, TraceRound } from "@/types/trace";

export const currentRound = (trace?: Trace | null): TraceRound | null => {
  if (!trace?.rounds?.length) return null;
  return trace.rounds.find((r) => !r.closed_at) ?? trace.rounds[trace.rounds.length - 1];
};

/**
 * Tổng sản lượng giờ của vòng — LẤY TỪ SERVER, không cộng mảng `hourly`.
 *
 * `round.hourly` chỉ là TRANG ĐẦU kể từ khi sổ giờ được tách khỏi cây truy cứu.
 * Cộng nó lại là ra con số hụt: đo trên một vòng 28 dòng, cộng trang đầu ra 10.864
 * trong khi tổng thật là 15.000. Mà con số này chặn "đóng thùng vượt số đã làm ra",
 * nên hụt là người vận hành bị chặn oan giữa ca.
 */
export const hourlyTotal = (round: TraceRound | null) => round?.hourly_qty_total ?? 0;

export const hourlyTargetTotal = (round: TraceRound | null) =>
  round?.hourly_target_total ?? 0;

export const isProductionClosed = (round: TraceRound | null) => Boolean(round?.production);

export const isPackingStarted = (round: TraceRound | null) => Boolean(round?.packing?.started_at);

export const isPackingDone = (round: TraceRound | null) => Boolean(round?.packing?.completed_at);

export const assignedLineCodes = (round: TraceRound | null) =>
  (round?.lines ?? []).map((l) => l.line_code);
