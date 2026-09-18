import { DataList } from "@/components/ui/DataList";
import { nfmt } from "@/utils/format";
import type { BoxReconcile } from "@/utils/packing";

type Props = {
  box: BoxReconcile;
  /** Trong ca thì cần biết sổ mở chưa; lúc chốt thì không, đã chắc là mở rồi. */
  packStarted?: boolean;
  /** Lúc chốt sổ hiện dòng tổng `Chênh`; trong ca hiện dòng `Chưa ghi sổ`. */
  showTotal?: boolean;
};

/**
 * Một bảng đối chiếu sổ thùng, dùng chung cho cả lúc ghi trong ca lẫn lúc chốt.
 * Hai chỗ đọc cùng một phép trừ nên phải hiện cùng một cách — viết hai lần là
 * sớm muộn hai chỗ nói hai con số khác nhau.
 */
export function BoxTally({ box, packStarted, showTotal }: Props) {
  return (
    <DataList
      rows={[
        ...(packStarted === undefined
          ? []
          : [{ k: "Sổ đóng thùng", v: packStarted ? "đã mở" : "chưa mở" }]),
        { k: "Đã ghi sổ thùng", v: `${box.boxesLogged} thùng · ${nfmt(box.packedPcs)} pcs` },
        { k: "Chuyền làm ra", v: `${nfmt(box.madePcs)} pcs` },
        ...(showTotal
          ? [{ k: "Chênh", v: `${nfmt(box.diffPcs)} pcs`, tone: "total" as const }]
          : box.unloggedBoxes
            ? [
                {
                  // Chỉ thùng ĐẦY chưa ghi mới là sổ chạy sau thực tế. Phần lẻ
                  // không bao giờ vào sổ giờ nên tô cảnh báo là báo động giả.
                  k: "Sổ giờ chạy sau",
                  v: `${box.unloggedBoxes} thùng`,
                  tone: "warn" as const,
                },
              ]
            : box.loosePcs
              ? [{ k: "Chưa đủ một thùng", v: `${nfmt(box.loosePcs)} pcs` }]
              : []),
      ]}
    />
  );
}
