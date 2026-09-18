import { z } from "zod";

/**
 * Câu lỗi mặc định của zod là tiếng Anh cho lập trình viên đọc, không phải cho
 * người đứng máy: ô để trống một lúc thì màn hình ngoài xưởng hiện
 * `Invalid input: expected number, received NaN`.
 *
 * Đặt ở MỘT chỗ và nạp từ `schemas/index` nên mọi schema — kể cả schema viết sau
 * này — đều được dịch, không ai phải nhớ gắn `message` cho từng trường.
 *
 * Chỉ dịch những câu lọt ra ngoài. Câu nào schema đã tự viết thì zod giữ nguyên
 * câu đó, vì nó nói đúng nghiệp vụ hơn bất kỳ câu chung nào.
 */
z.config({
  customError: (issue) => {
    if (issue.code === "invalid_type") {
      if (issue.expected === "number") return "Chưa nhập số";
      if (issue.expected === "string") return "Chưa nhập";
      return "Giá trị không hợp lệ";
    }
    if (issue.code === "too_small") return `Nhỏ hơn mức cho phép (${issue.minimum})`;
    if (issue.code === "too_big") return `Lớn hơn mức cho phép (${issue.maximum})`;
    if (issue.code === "invalid_format") return "Sai định dạng";
    return undefined;
  },
});

/** Ô số để trống cho ra `NaN` với `valueAsNumber`. Kiểu VÀO và RA đều là `number`
 *  nên `useForm<T>` vẫn khớp — `z.preprocess` hay `z.coerce` thì không. */
export const maybeNum = z.union([z.number(), z.nan()]);

export const isBlank = (n: number) => Number.isNaN(n);

/** Ô trống nghĩa là KHÔNG CÓ, không phải nhập sai: hỏng 0, thiếu 0, quy cách 0. */
export const orZero = (n: number) => (Number.isNaN(n) ? 0 : n);
