import { z } from "zod";

import { isBlank as blank, maybeNum } from "@/schemas/zodSetup";

/**
 * R8 — khớp backend hai chiều. Nguồn sự thật ghi ở FE-PLAN §4.3.
 *
 * KHÔNG kiểm `qty_ok + qty_ng + qty_short = mục tiêu vòng` ở đây: mục tiêu nằm
 * ở server và đổi theo vòng. Kiểm ở FE là có hai luật, và luật FE sẽ sai trước.
 * FE chỉ hiện TỔNG SỐNG cho người gõ thấy, rồi để trigger chặn.
 *
 * KHÔNG dùng `z.coerce.number()`: nó làm kiểu VÀO của schema là `unknown` còn
 * kiểu RA là `number`, và `useForm<T>` của RHF không khớp được hai kiểu đó.
 * Ô nhập là `type="number"` nên `register(..., { valueAsNumber: true })` đã đổi
 * kiểu hộ — chuyển đổi nằm ở một chỗ thay vì hai.
 */
/**
 * Sản lượng giờ và thùng giờ ghi CÙNG một lúc, nên một form một nút.
 *
 * Người đứng máy cuối giờ ghi hai con số bằng một lần cầm bút. Tách ra hai màn
 * hình là bắt họ nhảy tab giữa hai việc của cùng một thao tác.
 *
 * Ô trống với `valueAsNumber` cho ra `NaN`, mà `z.number()` từ chối NaN. Dùng
 * `z.union([z.number(), z.nan()])` để kiểu VÀO và kiểu RA đều là `number` —
 * `z.preprocess` hay `z.coerce` sẽ làm kiểu vào thành `unknown` và `useForm<T>`
 * không khớp được.
 */
export const shiftLogSchema = z
  .object({
    slot_hour: z.number().int().min(0).max(23),
    headcount: maybeNum,
    target_qty: maybeNum,
    qty: maybeNum,
    boxes: maybeNum,
  })
  .superRefine((v, ctx) => {
    if (blank(v.qty) && blank(v.boxes)) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ["qty"],
        message: "Chưa nhập gì — điền sản lượng thực tế hoặc số thùng.",
      });
      return;
    }
    if (!blank(v.qty)) {
      if (v.qty <= 0)
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          path: ["qty"],
          message: "Sản lượng thực tế phải lớn hơn 0",
        });
      // Ba số đi liền nhau: thiếu số người hay định mức thì không tính được
      // năng suất và phần trăm đạt, mà đó mới là thứ cuối ca người ta cần đọc.
      if (blank(v.headcount) || v.headcount <= 0)
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          path: ["headcount"],
          message: "Ghi sản lượng phải đủ ba số",
        });
      if (blank(v.target_qty) || v.target_qty <= 0)
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          path: ["target_qty"],
          message: "Ghi sản lượng phải đủ ba số",
        });
    }
    if (!blank(v.boxes) && v.boxes <= 0)
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ["boxes"],
        message: "Số thùng phải lớn hơn 0",
      });
  });
export type ShiftLogForm = z.infer<typeof shiftLogSchema>;

/**
 * Ba ô số của chốt sổ. Ô TRỐNG nghĩa là KHÔNG CÓ, không phải nhập sai — hỏng 0 và
 * thiếu 0 là trường hợp thường gặp nhất, bắt gõ số 0 vào là thừa một thao tác.
 *
 * Luật `đạt + hỏng + thiếu = mục tiêu vòng` (§7.5) KHÔNG nằm trong schema này, vì
 * mục tiêu đổi theo từng vòng và nó thuộc về server. Nhưng form vẫn phải chặn
 * trước khi gửi — xem `CloseBookForm`: nó kiểm bằng CHÍNH con số `target_qty`
 * server trả về, nên vẫn là một nguồn sự thật, chỉ là kiểm sớm hơn một nhịp.
 */
export const closeSchema = z
  .object({
    qty_ok: maybeNum,
    qty_ng: maybeNum,
    qty_short: maybeNum,
    ng_reason_text: z.string().optional(),
    short_reason_text: z.string().optional(),
  })
  .superRefine((v, ctx) => {
    for (const k of ["qty_ok", "qty_ng", "qty_short"] as const)
      if (!blank(v[k]) && v[k] < 0)
        ctx.addIssue({ code: z.ZodIssueCode.custom, path: [k], message: "Không được âm" });

    // CSDL có CHECK `ng_needs_reason` và `short_needs_reason`. Không kiểm ở đây
    // thì màn hình cho bấm rồi ăn 422 — mà lúc đó người ta đã gõ xong cả form.
    // Hỏng 500 vì lỗi khuôn, thiếu 1.000 vì chờ bù liệu: hai chuyện khác nhau,
    // và cuối tháng không ai truy ra được nếu bỏ trống (§7.5).
    const hasAny = (n: number) => !blank(n) && n > 0;
    if (hasAny(v.qty_ng) && !v.ng_reason_text?.trim())
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ["ng_reason_text"],
        message: "Có hàng hỏng thì bắt buộc ghi lý do",
      });
    if (hasAny(v.qty_short) && !v.short_reason_text?.trim())
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ["short_reason_text"],
        message: "Làm thiếu thì bắt buộc ghi lý do",
      });
  });
export type CloseForm = z.infer<typeof closeSchema>;
