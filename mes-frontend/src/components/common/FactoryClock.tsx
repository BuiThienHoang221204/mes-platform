"use client";

import { useEffect, useState } from "react";

export function FactoryClock() {
  const [now, setNow] = useState<string>("--:--");

  useEffect(() => {
    const tick = () => {
      const d = new Date();
      setNow(`${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`);
    };
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, []);

  return (
    <span className="flex items-center gap-2 rounded-field border border-line bg-surface-2 px-2 py-1.5 sm:px-3">
      <span className="hidden text-caption text-fg-subtle sm:inline">Giờ xưởng</span>
      <span className="text-body tnum text-fg">{now}</span>
    </span>
  );
}
