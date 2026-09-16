import { z } from "zod";

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
export const hourlySchema = z.object({
  slot_hour: z.number().int().min(0).max(23),
  headcount: z.number().int().positive("Số người phải lớn hơn 0"),
  target_qty: z.number().int().positive("Sản lượng yêu cầu phải lớn hơn 0"),
  qty: z.number().int().positive("Sản lượng thực tế phải lớn hơn 0"),
});
export type HourlyForm = z.infer<typeof hourlySchema>;

export const boxHourlySchema = z.object({
  slot_hour: z.number().int().min(0).max(23),
  boxes: z.number().int().positive("Số thùng phải lớn hơn 0"),
});
export type BoxHourlyForm = z.infer<typeof boxHourlySchema>;

export const closeSchema = z.object({
  qty_ok: z.number().int().min(0),
  qty_ng: z.number().int().min(0),
  qty_short: z.number().int().min(0),
  ng_reason_text: z.string().optional(),
  short_reason_text: z.string().optional(),
});
export type CloseForm = z.infer<typeof closeSchema>;
