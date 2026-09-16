"use client";

import { useUiStore } from "@/stores/useUiStore";

const TONE = {
  ok: "bg-ok-soft text-ok border-ok",
  warn: "bg-warn-soft text-warn border-warn",
  danger: "bg-danger-soft text-danger border-danger",
} as const;

/**
 * Toast neo ở ĐẦU trang.
 *
 * Trước đây nằm đáy màn: máy tính bảng dựng đứng trên bàn trạm thì mép dưới lọt
 * khỏi tầm mắt, mà người vừa bấm nút lại đang nhìn lên trên — báo lỗi ở đó là
 * báo cho không ai. `env(safe-area-inset-top)` để tránh tai thỏ khi chạy toàn màn.
 */
export function ToastHost() {
  const toasts = useUiStore((s) => s.toasts);
  const dismiss = useUiStore((s) => s.dismiss);
  if (!toasts.length) return null;

  return (
    <div className="pointer-events-none fixed inset-x-0 top-[calc(1rem+env(safe-area-inset-top))] z-50 flex flex-col items-center gap-2 px-4">
      {toasts.map((t) => (
        <button
          key={t.id}
          type="button"
          onClick={() => dismiss(t.id)}
          className={`pointer-events-auto max-w-2xl rounded-card border px-5 py-3 text-body font-medium shadow-lg ${TONE[t.kind]}`}
        >
          {t.text}
        </button>
      ))}
    </div>
  );
}
