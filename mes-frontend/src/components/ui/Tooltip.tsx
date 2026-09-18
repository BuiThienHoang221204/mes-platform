"use client";

import { useEffect, useId, useRef, useState, type ReactNode } from "react";
import { createPortal } from "react-dom";

type Side = "top" | "bottom";
type Spot = { center: number; y: number; side: Side };

type Props = {
  content: ReactNode;
  children: ReactNode;
  side?: Side;
  className?: string;
};

const DELAY = 300;
const GAP = 8;
const MAX_W = 280;

/**
 * Chú giải hiện khi rê chuột hoặc khi ô nhận tiêu điểm bàn phím.
 *
 * Thay cho `title=` của trình duyệt ở những chỗ cần đọc được: `title` do hệ điều
 * hành vẽ nên không nhận CSS của app, chờ tới hơn một giây mới hiện, tự tắt sau
 * vài giây, và KHÔNG hiện khi đi bằng bàn phím — người không dùng chuột mất hẳn
 * phần thông tin đó.
 *
 * Vẫn giữ `title` cho các dấu dày đặc trong biểu đồ: ở đó một chú giải có trạng
 * thái cho mỗi dấu là quá nhiều cho thứ người ta chỉ liếc qua.
 *
 * Vẽ qua portal vì thẻ có `overflow-hidden` để bo góc sẽ cắt mất khung nổi.
 */
export function Tooltip({ content, children, side = "top", className = "" }: Props) {
  const [spot, setSpot] = useState<Spot | null>(null);
  const anchor = useRef<HTMLSpanElement>(null);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const id = useId();

  const hide = () => {
    if (timer.current) clearTimeout(timer.current);
    timer.current = null;
    setSpot(null);
  };

  const show = () => {
    if (timer.current) clearTimeout(timer.current);
    timer.current = setTimeout(() => {
      const r = anchor.current?.getBoundingClientRect();
      if (!r) return;
      const half = MAX_W / 2;
      // Lật xuống dưới khi sát mép trên — không thì khung nổi ra ngoài màn hình.
      const at: Side = side === "top" && r.top < 64 ? "bottom" : side;
      setSpot({
        center: Math.max(half + 8, Math.min(r.left + r.width / 2, window.innerWidth - half - 8)),
        y: at === "top" ? r.top - GAP : r.bottom + GAP,
        side: at,
      });
    }, DELAY);
  };

  useEffect(() => {
    if (!spot) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") hide();
    };
    document.addEventListener("keydown", onKey);
    window.addEventListener("scroll", hide, true);
    window.addEventListener("resize", hide);
    return () => {
      document.removeEventListener("keydown", onKey);
      window.removeEventListener("scroll", hide, true);
      window.removeEventListener("resize", hide);
    };
  }, [spot]);

  useEffect(() => () => void (timer.current && clearTimeout(timer.current)), []);

  const bubble = spot ? (
    <div
      id={id}
      role="tooltip"
      style={{
        top: spot.y,
        left: spot.center,
        maxWidth: MAX_W,
        transform: `translate(-50%, ${spot.side === "top" ? "-100%" : "0"})`,
      }}
      className="pointer-events-none fixed z-[70] rounded-field bg-fg px-3 py-2 text-caption leading-snug text-bg shadow-lg"
    >
      {content}
    </div>
  ) : null;

  return (
    <>
      <span
        ref={anchor}
        aria-describedby={spot ? id : undefined}
        tabIndex={0}
        onMouseEnter={show}
        onMouseLeave={hide}
        onFocus={show}
        onBlur={hide}
        className={`inline-flex min-w-0 max-w-full ${className}`}
      >
        {children}
      </span>

      {bubble ? createPortal(bubble, document.body) : null}
    </>
  );
}
