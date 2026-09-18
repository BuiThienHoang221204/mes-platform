"use client";

import { useInfiniteQuery, useMutation, useQuery } from "@tanstack/react-query";
import { PAGE_SIZE } from "@/constants/pagination";
import { catalogKeys, moKeys } from "@/constants/queryKeys";
import { productionService, type ClosePayload, type HourlyPayload } from "@/services/production.service";
import { useInvalidateStation } from "@/hooks/useInvalidateStation";
import { useUiStore } from "@/stores/useUiStore";
import type { ApiError } from "@/types/api";
import type { TraceEvent } from "@/types/trace";

export const useTrace = (code: string | null) =>
  useQuery({
    queryKey: moKeys.trace(code ?? ""),
    queryFn: () => productionService.trace(code as string),
    enabled: !!code,
    staleTime: 5_000,
  });

/** Số dòng nhật ký mỗi lần bấm Xem thêm. Khớp `EVENT_PAGE` ở backend. */
export const EVENT_PAGE = PAGE_SIZE;

/**
 * Nhật ký một MO, tải dần theo trang.
 *
 * `trace` chỉ trả trang đầu — một MO chạy nhiều vòng có hàng trăm dòng, mà màn
 * hình chỉ hiện mười. Trang sau lấy ở đây khi người dùng bấm Xem thêm.
 *
 * `initialData` nhận trang đầu từ `trace` nên mở màn không tốn thêm request nào;
 * chỉ lúc bấm Xem thêm mới thật sự gọi mạng.
 */
export function useEvents(code: string | null, first: TraceEvent[], total: number) {
  return useInfiniteQuery({
    queryKey: moKeys.events(code ?? ""),
    enabled: !!code,
    initialPageParam: 0,
    queryFn: ({ pageParam }) =>
      productionService.events(code as string, EVENT_PAGE, pageParam),
    // Trang kế bắt đầu ngay sau số dòng đã tải. `undefined` = hết, TanStack tự
    // tắt `hasNextPage`, nên nút Xem thêm không cần tự đếm.
    getNextPageParam: (_last, pages) => {
      const loaded = pages.reduce((n, p) => n + p.items.length, 0);
      return loaded < (pages[0]?.total ?? total) ? loaded : undefined;
    },
    initialData: { pages: [{ items: first, total }], pageParams: [0] },
    staleTime: 5_000,
  });
}

/** Danh mục gần như không đổi — `staleTime: Infinity` (R4). */
export const useLines = () =>
  useQuery({ queryKey: catalogKeys.lines(), queryFn: productionService.lines, staleTime: Infinity });

/**
 * Tám mutation của trạm 4 dùng CHUNG một cách báo lỗi và một cách làm mới dữ liệu.
 *
 * Phần dùng chung nằm ở `sharedOptions` — một hàm THƯỜNG trả về object options,
 * KHÔNG phải hàm gọi `useMutation` hộ. Gọi hook bên trong helper là vi phạm
 * rules-of-hooks: nó chạy đúng hôm nay, nhưng thêm một nhánh `if` là vỡ.
 */
function useShared(code: string | null) {
  const invalidate = useInvalidateStation();
  const toast = useUiStore((s) => s.toast);

  // KHÔNG gắn generic cho options: ghim `TVariables` ở đây là nó lây sang mọi
  // mutation và biến tham số của chúng thành `never`.
  return () => ({
    onSuccess: (r: unknown) => {
      invalidate(code ?? undefined);
      const msg = (r as { message?: string })?.message;
      if (msg) toast(msg);
    },
    // `http.ts` bảo đảm mọi lỗi ném ra đã là `ApiError`.
    onError: (e: unknown) => toast((e as ApiError).message, "danger"),
  });
}

export function useProductionActions(code: string | null) {
  const shared = useShared(code);
  const mo = code as string;

  const assign = useMutation({
    mutationFn: (line: string) => productionService.assign(mo, line),
    ...shared(),
  });
  const start = useMutation({
    mutationFn: (line: string) => productionService.start(mo, line),
    ...shared(),
  });
  const hold = useMutation({
    mutationFn: (v: { line: string; reason: string }) => productionService.hold(mo, v.line, v.reason),
    ...shared(),
  });
  const close = useMutation({
    mutationFn: (p: ClosePayload) => productionService.close(mo, p),
    ...shared(),
  });
  const packHourly = useMutation({
    mutationFn: (p: { work_date: string; slot_hour: number; boxes: number }) =>
      productionService.packHourly(mo, p),
    ...shared(),
  });
  const packFinish = useMutation({
    mutationFn: (v: { qty: number; note: string }) => productionService.packFinish(mo, v.qty, v.note),
    ...shared(),
  });

  /**
   * Ghi sổ ca: sản lượng giờ và số thùng giờ, một thao tác của người dùng.
   *
   * Thứ tự KHÔNG đổi được: ghi sản lượng trước, thùng sau. Trigger
   * `packing_hourly_within_made` chặn đóng nhiều hơn số đã làm ra, mà số đã làm
   * ra chính là Σ sản lượng giờ — ghi thùng trước thì giờ nào cũng bị chặn.
   *
   * Sổ đóng thùng do BACKEND tự mở ở lần ghi thùng đầu tiên (`packing.open_book`),
   * nên ở đây không còn màn thử-rồi-mở-rồi-thử-lại. Một luật, một chỗ.
   */
  const logShift = useMutation({
    mutationFn: async (p: {
      work_date: string;
      hourly?: Omit<HourlyPayload, "work_date" | "note">;
      boxes?: { slot_hour: number; boxes: number };
    }) => {
      const parts: string[] = [];
      let hourlyDone = false;

      if (p.hourly) {
        const r = await productionService.hourly(mo, {
          ...p.hourly,
          work_date: p.work_date,
          note: null,
        });
        parts.push(r.message);
        hourlyDone = true;
      }

      if (p.boxes) {
        try {
          const r = await productionService.packHourly(mo, {
            ...p.boxes,
            work_date: p.work_date,
          });
          parts.push(r.message);
        } catch (e) {
          // Hai lần ghi, không chung một transaction. Phải nói rõ phần nào đã vào
          // sổ, nếu không người dùng gõ lại cả hai và ăn lỗi "khung giờ đã ghi rồi".
          const err = e as ApiError;
          throw hourlyDone
            ? { ...err, message: `Sản lượng giờ đã ghi xong. Số thùng thì chưa: ${err.message}` }
            : err;
        }
      }

      return { ok: true, message: parts.join(" · ") };
    },
    ...shared(),
  });

  return { assign, start, hold, close, logShift, packHourly, packFinish };
}
