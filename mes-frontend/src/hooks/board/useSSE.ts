"use client";

import { useQueryClient } from "@tanstack/react-query";
import { useEffect } from "react";

import { boardKeys } from "@/constants/queryKeys";
import { createStationSSE } from "@/services/sse";

/**
 * SSE hook cho trạm — thay thế polling 10s của useQueue/useAtStation.
 *
 * Khi server push "queue:changed", hook tự invalidate React Query cache
 * cho cả `queue` và `atStation` của trạm đó. React Query sẽ refetch
 * nếu có component đang mount và dùng dữ liệu đó.
 *
 * Fallback: nếu SSE mất kết nối, EventSource tự reconnect.
 * Nếu cần fallback mạnh hơn, giữ refetchInterval nhỏ trong useQueue/useAtStation.
 *
 * @example
 * function StationPage() {
 *   useSSE(2);  // Kích hoạt SSE cho trạm 2
 *   return <QueueList station={2} />;
 * }
 */
export function useSSE(station: number | null) {
  const qc = useQueryClient();

  useEffect(() => {
    if (station == null) return;

    return createStationSSE(station, {
      onQueueChanged: () => {
        // Invalidate cả hai query vì chúng dùng chung event
        qc.invalidateQueries({ queryKey: boardKeys.queue(station) });
        qc.invalidateQueries({ queryKey: boardKeys.atStation(station) });
      },
    });
  }, [station, qc]);
}
