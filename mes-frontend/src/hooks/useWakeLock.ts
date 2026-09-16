"use client";

import { useEffect } from "react";

/**
 * R28 — màn hình trạm không được ngủ. Máy tắt màn giữa ca là người ta phải cởi
 * găng để mở khoá. Hệ điều hành tự thu hồi khi tab mất focus nên phải requestLock lại.
 * Trình duyệt không hỗ trợ thì thôi — tiện nghi, không phải điều kiện.
 */
export function useWakeLock(enabled = true) {
  useEffect(() => {
    if (!enabled) return;
    let lock: WakeLockSentinel | null = null;
    let cancelled = false;

    const requestLock = async () => {
      try {
        lock = (await navigator.wakeLock?.request("screen")) ?? null;
      } catch { /* pin yếu hoặc không hỗ trợ — bỏ qua */ }
    };
    const onVisible = () => { if (document.visibilityState === "visible" && !cancelled) void requestLock(); };

    void requestLock();
    document.addEventListener("visibilitychange", onVisible);
    return () => {
      cancelled = true;
      document.removeEventListener("visibilitychange", onVisible);
      void lock?.release();
    };
  }, [enabled]);
}
