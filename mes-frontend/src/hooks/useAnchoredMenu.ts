"use client";

import { useCallback, useEffect, useRef, useState } from "react";

type Spot = { top: number; left: number; width: number };

/**
 * Khung nổi neo dưới một nút, vẽ vào `document.body` qua portal.
 *
 * Vẽ tại chỗ thì bị cắt: `AppCard` có `overflow-hidden` để bo góc cho bảng tràn
 * viền, mà `overflow-hidden` cắt cả phần tử `absolute`. Ra `body` thì không còn
 * phụ thuộc tổ tiên nào.
 *
 * Toạ độ tính một lần lúc mở, nên cuộn hay đổi cỡ cửa sổ là phải ĐÓNG — giữ lại
 * thì khung nổi trôi khỏi nút mà vẫn hiện.
 */
export function useAnchoredMenu(minWidth = 0) {
  const [spot, setSpot] = useState<Spot | null>(null);
  const anchor = useRef<HTMLButtonElement>(null);
  const menu = useRef<HTMLDivElement>(null);
  const open = spot !== null;

  const close = useCallback(() => setSpot(null), []);

  const toggle = useCallback(() => {
    if (spot) {
      setSpot(null);
      return;
    }
    const r = anchor.current?.getBoundingClientRect();
    if (!r) return;
    const width = Math.max(minWidth, r.width);
    setSpot({
      top: r.bottom + 4,
      left: Math.max(8, Math.min(r.left, window.innerWidth - width - 8)),
      width,
    });
  }, [spot, minWidth]);

  useEffect(() => {
    if (!open) return;
    const onOutside = (e: MouseEvent) => {
      const t = e.target as Node;
      if (!anchor.current?.contains(t) && !menu.current?.contains(t)) close();
    };
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") close();
    };
    document.addEventListener("mousedown", onOutside);
    document.addEventListener("keydown", onKey);
    window.addEventListener("scroll", close, true);
    window.addEventListener("resize", close);
    return () => {
      document.removeEventListener("mousedown", onOutside);
      document.removeEventListener("keydown", onKey);
      window.removeEventListener("scroll", close, true);
      window.removeEventListener("resize", close);
    };
  }, [open, close]);

  return { spot, open, anchor, menu, toggle, close };
}
