/** Mã lệnh: chữ M kèm đúng 6 chữ số — khớp CHECK `mo_code_format` của CSDL. */
export const MO_CODE_RE = /M\d{6}/;

/**
 * Lôi mã MO ra khỏi chuỗi QR đọc được.
 *
 * Không so khớp cả chuỗi vì ba lý do có thật ngoài xưởng: đầu đọc chèn ký tự
 * tiền tố, tem in kèm tên con hàng, và QR của một số tem là cả một URL. Tìm mã
 * bên trong chuỗi thì cả ba trường hợp đều chạy.
 */
export function readMoCode(raw: string): { code: string } | { error: string } {
  const m = raw.toUpperCase().match(MO_CODE_RE);
  if (!m) return { error: `Đọc được mã nhưng không phải mã lệnh: ${raw.slice(0, 40)}` };
  return { code: m[0] };
}
