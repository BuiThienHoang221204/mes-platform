"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";

import { AppButton } from "@/components/ui/AppButton";
import { AppInput } from "@/components/ui/AppInput";
import { DataList } from "@/components/ui/DataList";
import { Note } from "@/components/ui/Note";
import { closeSchema, type CloseForm as Form } from "@/schemas/production";
import { orZero } from "@/schemas/zodSetup";
import type { ClosePayload } from "@/services/production.service";
import { nfmt } from "@/utils/format";

type Props = {
  targetQty: number;
  hourlySum: number;
  busy?: boolean;
  onSubmit: (p: ClosePayload) => void;
};

export function CloseBookForm({ targetQty, hourlySum, busy, onSubmit }: Props) {
  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<Form>({
    resolver: zodResolver(closeSchema),
    defaultValues: { qty_ok: 0, qty_ng: 0, qty_short: 0 },
  });

  const ok = orZero(watch("qty_ok"));
  const ng = orZero(watch("qty_ng"));
  const short = orZero(watch("qty_short"));
  const ngReason = watch("ng_reason_text")?.trim() ?? "";
  const shortReason = watch("short_reason_text")?.trim() ?? "";
  const sum = ok + ng + short;
  const diff = sum - targetQty;

  // §7.2b — sản lượng giờ "cộng dồn, đối soát với SX ĐẠT của vòng". Backend cũng
  // hiểu vậy: `_made_pcs` lấy `qty_ok` khi đã chốt, chưa chốt thì tạm Σ giờ — hai
  // con số là MỘT đại lượng, đo ở hai thời điểm.
  //
  // Chỉ ĐỐI SOÁT, không chặn: sổ giờ là ghi tay, có ca không ai ghi đủ.
  const hourlyGap = hourlySum > 0 ? ok - hourlySum : 0;

  /**
   * Mọi điều kiện chặn, gom vào MỘT danh sách.
   *
   * Trước đây dải trạng thái chỉ kiểm phép cộng rồi hiện xanh "khớp mục tiêu
   * vòng" — người đọc hiểu là "hợp lệ, bấm đi", trong khi còn thiếu lý do bắt
   * buộc và nút vẫn sẽ bị CSDL từ chối. Một dải trạng thái phải nói về TOÀN BỘ
   * form, không phải về một phép tính trong đó.
   */
  const blockers: string[] = [];
  if (diff !== 0)
    blockers.push(
      `Σ ${nfmt(sum)}/${nfmt(targetQty)} — còn ${diff > 0 ? "dư" : "thiếu"} ${nfmt(Math.abs(diff))} pcs chưa khai`,
    );
  if (ng > 0 && !ngReason) blockers.push("Có hàng hỏng nhưng chưa ghi Lý do hỏng");
  if (short > 0 && !shortReason) blockers.push("Làm thiếu nhưng chưa ghi Lý do thiếu");

  const canClose = blockers.length === 0;

  // Ô trống nghĩa là KHÔNG CÓ. Hỏng 0 và thiếu 0 là trường hợp thường gặp nhất,
  // bắt người ta gõ số 0 vào là thừa một thao tác mỗi lần chốt sổ.
  const submit = handleSubmit((v) => {
    if (orZero(v.qty_ok) + orZero(v.qty_ng) + orZero(v.qty_short) !== targetQty) return;
    onSubmit({
      qty_ok: orZero(v.qty_ok),
      qty_ng: orZero(v.qty_ng),
      qty_short: orZero(v.qty_short),
      ng_reason_text: v.ng_reason_text?.trim() || null,
      short_reason_text: v.short_reason_text?.trim() || null,
    });
  });

  return (
    <form onSubmit={submit} className="space-y-4">
      <DataList
        rows={[
          { k: "Mục tiêu vòng", v: `${nfmt(targetQty)} pcs` },
          { k: "Σ sản lượng giờ đã ghi", v: `${nfmt(hourlySum)} pcs` },
        ]}
      />

      <div className="grid gap-4 sm:grid-cols-3">
        <AppInput
          label="Số lượng đạt"
          type="number"
          inputMode="numeric"
          error={errors.qty_ok?.message}
          {...register("qty_ok", { valueAsNumber: true })}
        />
        <AppInput
          label="Số lượng hỏng"
          type="number"
          inputMode="numeric"
          hint="làm ra rồi nhưng hỏng"
          error={errors.qty_ng?.message}
          {...register("qty_ng", { valueAsNumber: true })}
        />
        <AppInput
          label="Số lượng thiếu"
          type="number"
          inputMode="numeric"
          hint="không làm ra được"
          error={errors.qty_short?.message}
          {...register("qty_short", { valueAsNumber: true })}
        />
      </div>

      <Note tone={canClose ? "ok" : "danger"}>
        {canClose ? (
          <>
            <strong>Σ {nfmt(sum)} — khớp mục tiêu vòng, đủ lý do.</strong> Chốt sổ được rồi.
          </>
        ) : (
          <>
            <strong>Chưa chốt được — còn {blockers.length} chỗ:</strong>
            <ul className="mt-1 list-disc space-y-0.5 pl-5">
              {blockers.map((v) => (
                <li key={v}>{v}</li>
              ))}
            </ul>
            {diff !== 0 ? (
              <span className="mt-1 block">
                Mỗi cái giao xuống chuyền phải rơi vào đúng một trong ba nhóm: làm ra được
                (đạt), làm ra rồi nhưng hỏng, hoặc không làm ra được (thiếu).
              </span>
            ) : null}
          </>
        )}
      </Note>

      {diff === 0 && hourlyGap !== 0 ? (
        <Note tone="warn">
          <strong>
            Sổ sản lượng giờ ghi chuyền làm ra {nfmt(hourlySum)} pcs, nhưng bạn khai đạt{" "}
            {nfmt(ok)}
            {ng > 0 ? ` · hỏng ${nfmt(ng)}` : ""}
            {short > 0 ? ` · thiếu ${nfmt(short)}` : ""}.
          </strong>{" "}
          Hai sổ nói hai chuyện khác nhau về cùng một vòng, lệch {nfmt(Math.abs(hourlyGap))} pcs.
          Sổ giờ là ghi tay nên lệch được — nhưng chốt sổ không hoàn tác, nhìn lại một lượt
          trước khi bấm.
        </Note>
      ) : null}

      <div className="grid gap-4 sm:grid-cols-2">
        <AppInput
          label="Lý do hỏng"
          placeholder={ng > 0 ? "Bắt buộc — vì sao hỏng" : "Chỉ cần khi có hàng hỏng"}
          error={errors.ng_reason_text?.message}
          {...register("ng_reason_text")}
        />
        <AppInput
          label="Lý do thiếu"
          placeholder={short > 0 ? "Bắt buộc — vì sao không làm đủ" : "Chỉ cần khi làm thiếu"}
          error={errors.short_reason_text?.message}
          {...register("short_reason_text")}
        />
      </div>

      <AppButton type="submit" variant="primary" disabled={busy || !canClose}>
        Chốt sổ sản xuất
      </AppButton>

      <p className="text-caption text-fg-subtle">
        Hỏng và thiếu là hai chuyện khác nhau nên hỏi riêng. Làm thiếu mà không hỏng cái nào là
        chuyện rất thường. Mỗi vòng chỉ chốt sổ được một lần.
      </p>
    </form>
  );
}
