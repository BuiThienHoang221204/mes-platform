import { z } from "zod";

/**
 * R8 — khớp backend hai chiều:
 *   `^M\d{6}$`      → CHECK mo_code_format
 *   quantity > 0     → CHECK (quantity > 0)
 *   pcs_per_box ≥ 0  → CHECK (pcs_per_box >= 0), 0 = mặt hàng không đóng thùng
 */
export const moCreateSchema = z.object({
  code: z.string().regex(/^M\d{6}$/, "Mã phải là chữ M kèm đúng 6 chữ số"),
  product_name: z.string().trim().min(1, "Nhập tên con hàng"),
  quantity: z.number().int().positive("Số lượng phải lớn hơn 0"),
  required_production_min: z.number().int().positive("Thời gian yêu cầu phải lớn hơn 0"),
  pcs_per_box: z.number().int().min(0, "Quy cách không âm"),
});
export type MoCreateForm = z.infer<typeof moCreateSchema>;

export const lineCreateSchema = z.object({
  code: z.string().trim().regex(/^[A-Za-z0-9-]{1,10}$/, "Mã chuyền 1–10 ký tự chữ/số"),
  name: z.string().trim().optional(),
});
export type LineCreateForm = z.infer<typeof lineCreateSchema>;
