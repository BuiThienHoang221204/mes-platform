import { z } from "zod";

import { isBlank, maybeNum } from "@/schemas/zodSetup";

/**
 * R8 — khớp backend hai chiều:
 *   `^M\d{6}$`      → CHECK mo_code_format
 *   quantity > 0     → CHECK (quantity > 0)
 *   pcs_per_box ≥ 0  → CHECK (pcs_per_box >= 0), 0 = mặt hàng không đóng thùng
 */
export const moCreateSchema = z
  .object({
    code: z.string().regex(/^M\d{6}$/, "Mã phải là chữ M kèm đúng 6 chữ số"),
    product_name: z.string().trim().min(1, "Nhập tên con hàng"),
    quantity: maybeNum,
    required_production_min: maybeNum,
    // Quy cách 0 = mặt hàng không đóng thùng, nên ô trống hiểu là 0.
    pcs_per_box: maybeNum,
  })
  .superRefine((v, ctx) => {
    const requirePositive = (k: "quantity" | "required_production_min", ten: string) => {
      if (isBlank(v[k]) || v[k] <= 0)
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          path: [k],
          message: `${ten} phải lớn hơn 0`,
        });
    };
    requirePositive("quantity", "Số lượng");
    requirePositive("required_production_min", "Thời gian yêu cầu");
    if (!isBlank(v.pcs_per_box) && v.pcs_per_box < 0)
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ["pcs_per_box"],
        message: "Quy cách không âm",
      });
  });
export type MoCreateForm = z.infer<typeof moCreateSchema>;

export const lineCreateSchema = z.object({
  code: z.string().trim().regex(/^[A-Za-z0-9-]{1,10}$/, "Mã chuyền 1–10 ký tự chữ/số"),
  name: z.string().trim().optional(),
});
export type LineCreateForm = z.infer<typeof lineCreateSchema>;
