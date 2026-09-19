"use client";

import { useQuery, type UseQueryResult } from "@tanstack/react-query";
import { boardKeys } from "@/constants/queryKeys";
import { PAGE_SIZE } from "@/constants/pagination";
import { boardService } from "@/services/board.service";
import type { Page } from "@/types/api";

/** R4/R5 — bảng sống.
 *
 *  Hai mức, chia theo "ai đang chờ con số này":
 *
 *    LIVE 10s  hàng đợi, lệnh đang ở trạm, bảng đang chạy — người đứng trạm chờ
 *              việc, và bảng treo tường nhìn từ giữa xưởng
 *    SLOW 30s  badge số trên sidebar — không ai đứng nhìn nó
 *
 *  `staleTime` không để 0: toàn cục bật `refetchOnWindowFocus`, mà `staleTime: 0`
 *  nghĩa là LUÔN cũ — mỗi lần cửa sổ lấy lại focus là cả nhóm gọi lại ngay.
 *
 *  useQueue / useAtStation: SSE push thay polling → chỉ cần staleTime làm fallback.
 *  useRunning / useOverview: giữ refetchInterval vì chưa có SSE.
 */
const LIVE = { staleTime: 5_000, refetchInterval: 10_000 } as const;
/** SSE đã thay polling cho queue + atStation.
 *
 *  `staleTime: Infinity` — data KHÔNG bao giờ tự cũ. Fetch lần đầu khi mount,
 *  sau đó chỉ refetch khi:
 *    1. SSE push "queue:changed" → invalidateQueries
 *    2. Mutation (scan, handover, ...) → invalidateQueries
 *    3. refetch() thủ công từ component
 *
 *  Quay lại trang thì dùng cache, không gọi lại API. */
const SSE_LIVE = { staleTime: Infinity } as const;

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
    ...SSE_LIVE,
  }), limit);

/** Lệnh đang nằm trong tay trạm — quét xong thì nó rơi vào đây, không biến mất. */
export const useAtStation = (station: number | null) =>
  paged(useQuery({
    queryKey: boardKeys.atStation(station ?? -1),
    queryFn: () => boardService.atStation(station as number),
    enabled: station !== null,
    ...SSE_LIVE,
  }));

export const useOverview = () =>
  useQuery({ queryKey: boardKeys.overview(), queryFn: boardService.overview, ...LIVE });

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
