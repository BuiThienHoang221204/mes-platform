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
export const boxBreakdown = (pcs: number, pcsPerBox: number) => {
  if (!pcsPerBox) return `${nfmt(pcs)} pcs`;
  const full = Math.floor(pcs / pcsPerBox);
  const rest = pcs % pcsPerBox;
  const parts: string[] = [];
  if (full) parts.push(`${full} thùng đầy`);
  if (rest) parts.push(`1 thùng lẻ ${nfmt(rest)}`);
  return `${nfmt(pcs)} pcs = ${parts.join(" + ") || "0 thùng"}`;
};
