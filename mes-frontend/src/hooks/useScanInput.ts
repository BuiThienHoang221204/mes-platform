"use client";

import { useCallback, useEffect, useRef } from "react";

/**
 * §1 — ô quét phải auto-focus và LUÔN GIÀNH LẠI focus.
 * Đầu đọc QR là bàn phím: nó gõ rất nhanh rồi Enter. Mất focus một nhịp là
 * ký tự rơi vào chỗ khác và lần quét đó mất trắng.
 */
export function useScanInput(onSubmit: (raw: string) => void, enabled = true) {
  const ref = useRef<HTMLInputElement>(null);

  const keepFocus = useCallback(() => {
    if (!enabled) return;
    const el = ref.current;
    if (el && document.activeElement !== el) el.focus();
  }, [enabled]);

  useEffect(() => {
    keepFocus();
    const t = setInterval(keepFocus, 1200);
    window.addEventListener("click", keepFocus);
    return () => { clearInterval(t); window.removeEventListener("click", keepFocus); };
  }, [keepFocus]);

  const onKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key !== "Enter") return;
    e.preventDefault();
    const raw = e.currentTarget.value.trim();
    if (!raw) return;
    e.currentTarget.value = "";
    onSubmit(raw);
  };

  return { ref, onKeyDown };
}
