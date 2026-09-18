"use client";

import { useRouter } from "next/navigation";
import { Suspense, useEffect, type ReactNode } from "react";

import { AppTopbar } from "@/components/common/AppTopbar";
import { StationSidebar } from "@/components/common/StationSidebar";
import { useWakeLock } from "@/hooks/useWakeLock";
import { useSessionStore } from "@/stores/useSessionStore";

export default function StationLayout({ children }: { children: ReactNode }) {
  const router = useRouter();
  const checked = useSessionStore((s) => s.checked);
  const fullName = useSessionStore((s) => s.fullName);

  useWakeLock();

  useEffect(() => {
    if (checked && !fullName) router.replace("/login");
  }, [checked, fullName, router]);

  if (!checked || !fullName) return null;

  return (
    <div className="flex h-dvh overflow-hidden">
      <Suspense fallback={null}>
        <StationSidebar />
      </Suspense>
      <div className="flex min-w-0 flex-1 flex-col overflow-hidden">
        <Suspense fallback={null}>
          <AppTopbar />
        </Suspense>
        <main className="no-scrollbar min-w-0 flex-1 overflow-y-auto overflow-x-hidden px-6 py-6">{children}</main>
      </div>
    </div>
  );
}
