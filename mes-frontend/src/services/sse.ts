/**
 * SSE service — tạo EventSource kết nối đến server, tự reconnect khi mất kết nối.
 *
 * Server push event "queue:changed" khi hàng đợi hoặc lệnh tại trạm thay đổi.
 * Client gọi onQueueChanged để invalidate React Query cache.
 *
 * EventSource API:
 * - Gửi cookie httpOnly tự động (same-origin, samesite=lax)
 * - Tự reconnect khi mất kết nối
 * - Không hỗ trợ custom headers → dùng cookie là primary auth
 */

const RECONNECT_DELAY = 3_000;
const MAX_RECONNECT_DELAY = 30_000;

type StationSSEOptions = {
  onQueueChanged: () => void;
  onError?: (event: Event) => void;
};

/**
 * Tạo SSE connection cho một trạm. Trả về hàm disconnect.
 *
 * @example
 * const disconnect = createStationSSE(2, {
 *   onQueueChanged: () => qc.invalidateQueries(boardKeys.queue(2)),
 * });
 * // later: disconnect();
 */
export function createStationSSE(
  station: number,
  options: StationSSEOptions,
): () => void {
  let es: EventSource | null = null;
  let stopped = false;
  let reconnectDelay = RECONNECT_DELAY;
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null;

  function connect() {
    if (stopped) return;

    es = new EventSource(`/v1/sse/${station}`, {
      withCredentials: true,
    });

    es.addEventListener("queue:changed", () => {
      options.onQueueChanged();
      reconnectDelay = RECONNECT_DELAY; // Reset delay on successful message
    });

    es.addEventListener("keepalive", () => {
      reconnectDelay = RECONNECT_DELAY;
    });

    es.onerror = (event) => {
      options.onError?.(event);
      es?.close();
      es = null;

      if (!stopped) {
        reconnectTimer = setTimeout(() => {
          reconnectDelay = Math.min(reconnectDelay * 2, MAX_RECONNECT_DELAY);
          connect();
        }, reconnectDelay);
      }
    };
  }

  connect();

  return () => {
    stopped = true;
    if (reconnectTimer) {
      clearTimeout(reconnectTimer);
      reconnectTimer = null;
    }
    es?.close();
    es = null;
  };
}
