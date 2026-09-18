"use client";

import type { ReactNode } from "react";

import { useWakeLock } from "@/hooks/useWakeLock";

export default function BoardLayout({ children }: { children: ReactNode }) {
  useWakeLock();
  return <div className="min-h-dvh bg-bg">{children}</div>;
}
