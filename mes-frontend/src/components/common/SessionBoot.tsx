"use client";

import type { ReactNode } from "react";

import { useBootSession } from "@/hooks/auth/useSession";

export function SessionBoot({ children }: { children: ReactNode }) {
  useBootSession();
  return <>{children}</>;
}
