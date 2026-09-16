"use client";

import { useQueryClient } from "@tanstack/react-query";
import { boardKeys, moKeys } from "@/constants/queryKeys";

/**
 * R3 — MỌI thao tác ở trạm đều đổi hàng đợi và con số trên thanh trạm.
 * Gom vào một chỗ thay vì chép ba dòng `invalidateQueries` vào 12 hook.
 */
export function useInvalidateStation() {
  const qc = useQueryClient();
  return (code?: string) => {
    qc.invalidateQueries({ queryKey: boardKeys.all });
    if (code) {
      qc.invalidateQueries({ queryKey: moKeys.detail(code) });
      qc.invalidateQueries({ queryKey: moKeys.trace(code) });
    }
  };
}
