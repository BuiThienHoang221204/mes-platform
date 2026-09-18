"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";

import { BoxTally } from "@/components/packing/BoxTally";
import { AppButton } from "@/components/ui/AppButton";
import { AppCard } from "@/components/ui/AppCard";
import { AppInput } from "@/components/ui/AppInput";
import { AppSelect } from "@/components/ui/AppSelect";
import { shiftLogSchema, type ShiftLogForm } from "@/schemas/production";
import type { TraceRound } from "@/types/trace";
import { currentSlot, nfmt, slotLabel, today } from "@/utils/format";
import type { BoxReconcile } from "@/utils/packing";

const SLOTS = Array.from({ length: 24 }, (_, h) => ({ value: h, label: slotLabel(h) }));
const blank = (n: number) => Number.isNaN(n);

type Props = {
  round: TraceRound;
  pcsPerBox: number;
  box: BoxReconcile;
  packStarted: boolean;
  busy?: boolean;
  onLog: (p: {
    hourly?: { slot_hour: number; headcount: number; target_qty: number; qty: number };
    boxes?: { slot_hour: number; boxes: number };
    work_date: string;
  }) => void;
};

/**
 * Một form, hai sổ. Người đứng máy cuối giờ ghi hai con số bằng một lần cầm bút —
 * tách thành hai màn hình là bắt họ nhảy tab giữa hai việc của cùng một thao tác.
 */
export function ShiftLog({ round, pcsPerBox, box, packStarted, busy, onLog }: Props) {
  const {
    register,
    handleSubmit,
    watch,
    reset,
    setError,
    formState: { errors },
  } = useForm<ShiftLogForm>({
    resolver: zodResolver(shiftLogSchema),
    defaultValues: { slot_hour: currentSlot() },
  });

  const headcount = watch("headcount");
  const target = watch("target_qty");
  const qty = watch("qty");

  const rate = target > 0 && qty > 0 ? Math.round((qty / target) * 100) : null;
  const perHead = headcount > 0 && qty > 0 ? (qty / headcount).toFixed(1) : null;

  /**
   * Trần số thùng ghi được NGAY BÂY GIỜ — trigger `packing_hourly_within_made`
   * chặn đóng nhiều hơn số đã làm ra. Cộng cả số đang gõ ở cột trái vào: hai ô
   * nằm chung một form nên khai sản lượng và ghi thùng cùng lúc là hợp lệ, và
   * backend ghi sản lượng trước.
   */
  const addedQty = blank(qty) || qty < 0 ? 0 : qty;
  const roomPcs = Math.max(0, box.madePcs + addedQty - box.packedPcs);
  const maxBoxes = pcsPerBox > 0 ? Math.floor(roomPcs / pcsPerBox) : 0;
  const roomLoose = pcsPerBox > 0 ? roomPcs % pcsPerBox : 0;

  const submit = handleSubmit((v) => {
    if (!blank(v.boxes) && pcsPerBox > 0 && v.boxes > maxBoxes) {
      setError("boxes", {
        message:
          `Tối đa ${maxBoxes} thùng lúc này — mới làm ra ${nfmt(roomPcs)} pcs chưa đóng` +
          (roomLoose ? ` (${maxBoxes} thùng + ${nfmt(roomLoose)} lẻ)` : "") +
          `. Nếu thật sự đã đóng ${v.boxes} thùng thì khai Sản lượng thực tế cho đủ ở cột bên trái — không đóng thùng hàng chưa khai là đã làm ra.`,
      });
      return;
    }
    onLog({
      work_date: today(),
      hourly: blank(v.qty)
        ? undefined
        : {
            slot_hour: v.slot_hour,
            headcount: v.headcount,
            target_qty: v.target_qty,
            qty: v.qty,
          },
      boxes: blank(v.boxes) ? undefined : { slot_hour: v.slot_hour, boxes: v.boxes },
    });
    reset({ slot_hour: v.slot_hour });
  });

  const logged = round.hourly?.length ?? 0;

  return (
    <AppCard
      title="Trong ca"
      meta={logged ? `ghi lại mỗi giờ · đã ghi ${logged} giờ` : "ghi lại mỗi giờ"}
    >
      <form onSubmit={submit} className="space-y-5">
        <div className="sm:max-w-xs">
          <AppSelect
            label="Khung giờ"
            options={SLOTS}
            error={errors.slot_hour?.message}
            {...register("slot_hour", { valueAsNumber: true })}
          />
        </div>

        <div className="grid gap-5 lg:grid-cols-2 lg:gap-6">
          <div>
            <div className="mb-3 border-b border-line pb-2 text-label uppercase tracking-wider text-fg-subtle">
              Chuyền
            </div>
            <div className="space-y-3">
              <AppInput
                label="Số người đứng chuyền"
                type="number"
                inputMode="numeric"
                error={errors.headcount?.message}
                {...register("headcount", { valueAsNumber: true })}
              />
              <AppInput
                label="Sản lượng yêu cầu"
                type="number"
                inputMode="numeric"
                error={errors.target_qty?.message}
                {...register("target_qty", { valueAsNumber: true })}
              />
              <AppInput
                label="Sản lượng thực tế"
                type="number"
                inputMode="numeric"
                error={errors.qty?.message}
                {...register("qty", { valueAsNumber: true })}
              />
            </div>
            <p className="mt-2 text-caption text-fg-subtle">
              Đạt{" "}
              <strong className={rate != null && rate < 100 ? "text-warn" : "text-ok"}>
                {rate != null ? `${rate}%` : "—"}
              </strong>{" "}
              · Năng suất <strong className="text-fg">{perHead ?? "—"}</strong> cái/người — hệ
              thống tự tính, không có ô nhập.
            </p>
          </div>

          <div>
            <div className="mb-3 border-b border-line pb-2 text-label uppercase tracking-wider text-fg-subtle">
              Đóng thùng
            </div>
            {pcsPerBox > 0 ? (
              <>
                <AppInput
                  label="Số thùng ĐẦY đóng được"
                  type="number"
                  inputMode="numeric"
                  error={errors.boxes?.message}
                  hint={
                    maxBoxes
                      ? `quy cách ${nfmt(pcsPerBox)} pcs/thùng — tối đa ${maxBoxes} thùng lúc này`
                      : `quy cách ${nfmt(pcsPerBox)} pcs/thùng — chưa đủ một thùng, khai sản lượng thêm đã`
                  }
                  {...register("boxes", { valueAsNumber: true })}
                />
                <p className="mt-2 text-caption text-fg-subtle">
                  {packStarted
                    ? "Sổ đóng thùng đã mở. Hàng chưa đủ thùng để trên bàn, giờ sau gom tiếp."
                    : "Không có nút Bắt đầu đóng thùng riêng — gõ số thùng đầu tiên là sổ tự mở, và nhật ký ghi lại mốc đó."}
                </p>

                <div className="mt-4">
                  <BoxTally box={box} packStarted={packStarted} />
                </div>
              </>
            ) : (
              <p className="text-body-sm text-fg-muted">
                Lệnh này khai quy cách 0 — không đếm thùng. Bỏ qua nhánh này.
              </p>
            )}
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-4">
          <AppButton type="submit" variant="primary" disabled={busy}>
            Ghi cho giờ này
          </AppButton>
          <p className="text-body-sm text-fg-muted">
            Một nút, hai sổ. Bỏ trống bên nào thì bên đó không ghi.
          </p>
        </div>
      </form>
    </AppCard>
  );
}
