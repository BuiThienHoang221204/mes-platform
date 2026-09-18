"use client";

import { useRouter } from "next/navigation";
import { Suspense, useCallback, useEffect, useState, type ReactNode } from "react";

import { AppTopbar } from "@/components/common/AppTopbar";
import { StationSidebar } from "@/components/common/StationSidebar";
import { useWakeLock } from "@/hooks/useWakeLock";
import { useSessionStore } from "@/stores/useSessionStore";
import { useUiStore } from "@/stores/useUiStore";

export default function StationLayout({ children }: { children: ReactNode }) {
  const router = useRouter();
  const checked = useSessionStore((s) => s.checked);
  const fullName = useSessionStore((s) => s.fullName);
  const [navOpen, setNavOpen] = useState(false);
  const navCollapsed = useUiStore((s) => s.navCollapsed);
  const setNavCollapsed = useUiStore((s) => s.setNavCollapsed);

  useWakeLock();

  const closeNav = useCallback(() => setNavOpen(false), []);
  const openNav = useCallback(() => setNavOpen(true), []);
  const collapseNav = useCallback(() => setNavCollapsed(true), [setNavCollapsed]);
  const expandNav = useCallback(() => setNavCollapsed(false), [setNavCollapsed]);

  useEffect(() => {
    if (checked && !fullName) router.replace("/login");
  }, [checked, fullName, router]);

  if (!checked || !fullName) return null;

  return (
    <div className="flex min-h-dvh lg:h-dvh lg:overflow-hidden">
      <Suspense fallback={null}>
        <StationSidebar
          open={navOpen}
          collapsed={navCollapsed}
          onClose={closeNav}
          onCollapse={collapseNav}
          onExpand={expandNav}
        />
      </Suspense>
      <div className="flex min-w-0 flex-1 flex-col lg:overflow-hidden">
        <Suspense fallback={null}>
          <AppTopbar onMenu={openNav} />
        </Suspense>
        <main className="no-scrollbar min-w-0 flex-1 px-3 pb-[calc(2.5rem+env(safe-area-inset-bottom))] pt-5 sm:px-4 lg:overflow-y-auto lg:overflow-x-hidden lg:px-6 lg:py-6">
          {children}
        </main>
      </div>
    </div>
  );
}
