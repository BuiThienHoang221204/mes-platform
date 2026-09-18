import type { PillTone } from "@/constants/status";
import type { Trace, TraceRound } from "@/types/trace";
import { nfmt } from "@/utils/format";
import type { BoxReconcile } from "@/utils/packing";
import { hourlyTotal, isPackingDone, isProductionClosed } from "@/utils/trace";

/**
 * Câu trả lời cho "giờ tôi bấm cái nào".
 *
 * Trạm 4 có bảy màn hình và không màn nào nói việc kế tiếp là gì, nên người mới
 * bấm lần lượt 1→2→3 rồi tưởng đã xong quy trình trong khi chưa nhập gì. Suy
 * trạng thái ở một chỗ, hiện một câu, để onboarding tự chạy.
 */
export type NextAction = {
  tone: PillTone;
  label: string;
  title: string;
  hint: string;
  /** Khối cần cuộn tới. `null` khi không còn việc gì. */
  goto: "lines" | "shift" | "end" | null;
};

export function nextAction(
  trace: Trace,
  round: TraceRound,
  box: BoxReconcile,
): NextAction {
  const lines = round.lines ?? [];
  const running = lines.filter((l) => l.current_kind === "RUN");
  const held = lines.filter((l) => l.current_kind === "WAIT" && l.hold_reason_text);
  const idle = lines.filter((l) => l.current_kind === "WAIT" && !l.hold_reason_text);

  if (!lines.length)
    return {
      tone: "accent",
      label: "Việc tiếp theo",
      title: "Chọn chuyền cho lệnh này",
      hint: "Tick những chuyền sẽ chạy rồi bấm Thêm. Từ lúc đó đồng hồ thời gian chờ bắt đầu đếm.",
      goto: "lines",
    };

  if (held.length)
    return {
      tone: "danger",
      label: "Cần xử lý",
      title: `Chuyền ${held.map((l) => l.line_code).join(", ")} đang dừng`,
      hint: `${held[0].hold_reason_text}. Thời gian thực tế đang đứng. Cho chạy lại, hoặc trả lệnh về Bàn team leader nếu dừng quá lâu.`,
      goto: "lines",
    };

  if (!running.length && !isProductionClosed(round))
    return {
      tone: "accent",
      label: "Việc tiếp theo",
      title: `Cho ${idle.length > 1 ? `${idle.length} chuyền` : idle[0]?.line_code ?? "chuyền"} vào Đang lắp ráp`,
      hint: "Thời gian thực tế chỉ đếm khi chuyền chạy. Chưa chạy thì chưa ghi sản lượng được.",
      goto: "lines",
    };

  if (!isProductionClosed(round)) {
    const sum = hourlyTotal(round);
    if (sum >= round.target_qty)
      return {
        tone: "accent",
        label: "Việc tiếp theo",
        title: "Chốt sổ sản xuất",
        hint: `Σ sản lượng giờ đã đạt ${nfmt(sum)}/${nfmt(round.target_qty)} pcs. Khai đạt · hỏng · thiếu để chốt vòng.`,
        goto: "end",
      };
    return {
      tone: "accent",
      label: "Việc tiếp theo",
      title: "Ghi sản lượng giờ này",
      hint:
        `Cuối mỗi giờ ghi một lần, ghi luôn số thùng đóng được — cùng một nút.` +
        (round.hourly?.length
          ? ` Đã ghi ${round.hourly.length} giờ · ${nfmt(sum)}/${nfmt(round.target_qty)} pcs.`
          : ""),
      goto: "shift",
    };
  }

  if (isPackingDone(round))
    return {
      tone: "ok",
      label: "Xong việc của trạm 4",
      title: "Chờ Kho nhập quét nhận",
      hint: "Lệnh đã nằm ở hàng đợi Kho nhập. Không còn việc gì ở trạm này.",
      goto: null,
    };

  if (!trace.pcs_per_box)
    return {
      tone: "accent",
      label: "Việc tiếp theo",
      title: "Kết thúc đóng thùng",
      hint: "Lệnh này khai quy cách 0 — không đếm thùng. Ghi thẳng tổng pcs đã đóng.",
      goto: "end",
    };

  // Chỉ thùng ĐẦY chưa ghi mới đáng gọi ra. Phần lẻ không bao giờ vào sổ giờ —
  // nó vào thùng lẻ cuối lúc chốt (§7b.2), gọi nó là việc phải xử lý là báo động
  // giả, và báo động giả thì người ta học cách bỏ qua cả báo động thật.
  if (box.unloggedBoxes > 0)
    return {
      tone: "warn",
      label: "Nên xử lý",
      title: `Sổ giờ chạy sau thực tế ${box.unloggedBoxes} thùng`,
      hint: `Chuyền làm ra ${nfmt(box.madePcs)} pcs nhưng sổ thùng theo giờ mới ghi ${nfmt(box.packedPcs)}. Chốt vẫn đúng, nhưng ghi bù thì báo cáo sản lượng theo giờ mới đọc được.`,
      goto: "end",
    };

  return {
    tone: "accent",
    label: "Việc tiếp theo",
    title: "Kết thúc đóng thùng",
    hint: box.loosePcs
      ? `${nfmt(box.loosePcs)} pcs chưa đủ một thùng sẽ vào thùng lẻ cuối. Chốt xong lệnh sang hàng đợi Kho nhập.`
      : "Sổ thùng đã khớp sản lượng chuyền. Chốt xong lệnh sang hàng đợi Kho nhập.",
    goto: "end",
  };
}
