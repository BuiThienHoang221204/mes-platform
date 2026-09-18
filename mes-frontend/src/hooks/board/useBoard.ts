"use client";

import { useQuery, type UseQueryResult } from "@tanstack/react-query";
import { boardKeys } from "@/constants/queryKeys";
import { PAGE_SIZE } from "@/constants/pagination";
import { boardService } from "@/services/board.service";
import type { Page } from "@/types/api";

/** R4/R5 — bảng sống thì `refetchInterval`, KHÔNG `setInterval` thủ công.
 *
 *  Hai mức, chia theo "ai đang chờ con số này":
 *
 *    LIVE 10s  hàng đợi, lệnh đang ở trạm, bảng đang chạy — người đứng trạm chờ
 *              việc, và bảng treo tường nhìn từ giữa xưởng
 *    SLOW 30s  badge số trên sidebar — không ai đứng nhìn nó
 *
 *  `staleTime` không để 0: toàn cục bật `refetchOnWindowFocus`, mà `staleTime: 0`
 *  nghĩa là LUÔN cũ — mỗi lần cửa sổ lấy lại focus là cả nhóm gọi lại ngay, cộng
 *  thêm vào nhịp định kỳ. Cái giữ bảng sống là `refetchInterval`, không phải nó.
 */
const LIVE = { staleTime: 5_000, refetchInterval: 10_000 } as const;

/** Mở sẵn `items` và `total` — nơi gọi không phải viết `data?.items ?? []` mười hai lần.
 *
 *  `total` là tổng SAU LỌC, không phải số dòng trong trang — ba màn bảng dùng nó để
 *  hiện "còn n lệnh nữa" thay vì lặng lẽ cắt bớt. */
const paged = <T,>(q: UseQueryResult<Page<T>>, limit = PAGE_SIZE, offset = 0) => ({
  ...q,
  items: q.data?.items ?? [],
  total: q.data?.total ?? 0,
  limit,
  offset,
});
const SLOW = { staleTime: 20_000, refetchInterval: 30_000 } as const;

export const useQueue = (station: number | null, limit = PAGE_SIZE) =>
  paged(useQuery({
    queryKey: [...boardKeys.queue(station ?? -1), limit],
    queryFn: () => boardService.queue(station as number, limit),
    enabled: station !== null,
    ...LIVE,
  }), limit);

/** Lệnh đang nằm trong tay trạm — quét xong thì nó rơi vào đây, không biến mất. */
export const useAtStation = (station: number | null) =>
  paged(useQuery({
    queryKey: boardKeys.atStation(station ?? -1),
    queryFn: () => boardService.atStation(station as number),
    enabled: station !== null,
    ...LIVE,
  }));

export const useCounts = (range?: { from: string; to: string }) =>
  useQuery({
    queryKey: boardKeys.counts(range?.from, range?.to),
    queryFn: () => boardService.counts(range?.from, range?.to),
    ...SLOW,
  });

/** Bảng đang chạy có chuyển trang, và vẫn tự làm mới mỗi 10 giây.
 *
 *  Hai thứ này sống chung được vì `offset` nằm TRONG khoá query: làm mới chỉ nạp lại
 *  đúng trang đang xem, không kéo ai về trang 1. Cái còn lại phải lo là trang cuối
 *  rỗng đi khi lệnh đóng bớt — `RunningTable` kéo `offset` về khi điều đó xảy ra.
 *
 *  `queryFn` phải bọc trong hàm: React Query truyền `QueryFunctionContext` vào tham
 *  số đầu, để trần `boardService.running` thì `limit` nhận nguyên cục context đó. */
export const useRunning = (offset = 0, limit = PAGE_SIZE) =>
  paged(useQuery({
    queryKey: boardKeys.running(offset, limit),
    queryFn: () => boardService.running(limit, offset),
    ...LIVE,
  }), limit, offset);
