/** Số lượng luôn hiện theo kiểu Việt: 10.000 chứ không 10,000. */
export const nfmt = (n: number | null | undefined) =>
  n == null ? "—" : n.toLocaleString("vi-VN");

export const slotLabel = (h: number) =>
  `${String(h).padStart(2, "0")}:00–${String((h + 1) % 24).padStart(2, "0")}:00`;

/** Giờ hiện tại của máy, dùng làm mặc định cho ô khung giờ. */
export const currentSlot = () => new Date().getHours();

export const today = () => new Date().toISOString().slice(0, 10);

export const dur = (sec: number | null | undefined) => {
  if (sec == null) return "—";
  const h = Math.floor(sec / 3600);
  const m = Math.floor((sec % 3600) / 60);
  return h > 0 ? `${h} giờ ${m} phút` : `${m} phút`;
};

/**
 * Chia pcs ra thùng — CHỈ để HIỆN, không bao giờ để tính tiến độ (R23).
 * Thùng cuối của đơn được đóng thiếu (§7b.2), nên phần dư là một thùng lẻ.
 */
/**
 * Tách pcs ra thùng đầy và thùng lẻ — phép tính thuần, không dựng chữ.
 *
 * THÙNG CUỐI của đơn được đóng THIẾU (§7b.2) — đó là mặc định chứ không phải ngoại lệ,
 * vì đơn hàng hiếm khi chia hết cho quy cách. Nên 4.750 với quy cách 800 là
 * `5 thùng đầy + 1 thùng lẻ 750`, không phải "5,94 thùng".
 *
 * `pcsPerBox = 0` là mặt hàng KHÔNG ĐÓNG THÙNG — trả `null` để nơi gọi buộc phải
 * phân nhánh, thay vì lặng lẽ hiện "0 thùng" cho thứ không đếm bằng thùng.
 */
export const boxesOf = (pcs: number, pcsPerBox: number) =>
  pcsPerBox > 0
    ? { full: Math.floor(pcs / pcsPerBox), rest: pcs % pcsPerBox }
    : null;

/** Số thùng gọn một dòng: `6 thùng` · `5 thùng + 1 lẻ`. */
export const boxLabel = (pcs: number, pcsPerBox: number) => {
  const b = boxesOf(pcs, pcsPerBox);
  if (!b) return "không đóng thùng";
  if (!b.rest) return `${nfmt(b.full)} thùng`;
  return b.full ? `${nfmt(b.full)} thùng + 1 lẻ` : "1 thùng lẻ";
};

export const boxBreakdown = (pcs: number, pcsPerBox: number) => {
  const b = boxesOf(pcs, pcsPerBox);
  if (!b) return `${nfmt(pcs)} pcs`;
  const parts: string[] = [];
  if (b.full) parts.push(`${b.full} thùng đầy`);
  if (b.rest) parts.push(`1 thùng lẻ ${nfmt(b.rest)}`);
  return `${nfmt(pcs)} pcs = ${parts.join(" + ") || "0 thùng"}`;
};
