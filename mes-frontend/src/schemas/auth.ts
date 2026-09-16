import { z } from "zod";

/** R8 — khớp backend: `emp_code` là khoá duy nhất, `pin` băm bcrypt phía server. */
export const loginSchema = z.object({
  emp_code: z.string().trim().min(1, "Nhập mã nhân viên"),
  pin: z.string().min(4, "Mã PIN ít nhất 4 số"),
});

export type LoginForm = z.infer<typeof loginSchema>;
