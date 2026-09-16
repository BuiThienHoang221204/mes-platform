"use client";

import { useEffect } from "react";
import { useMutation } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { authService } from "@/services/auth.service";
import { setOnLogout } from "@/services/axiosConfig";
import { useSessionStore } from "@/stores/useSessionStore";
import { useUiStore } from "@/stores/useUiStore";
import type { ApiError } from "@/types/api";

/** Hỏi lại server một lần khi mở app — KHÔNG persist quyền vào localStorage. */
export function useBootSession() {
  const { setSession, clear, checked } = useSessionStore();
  const router = useRouter();

  useEffect(() => {
    setOnLogout(() => { clear(); router.replace("/login"); });
  }, [clear, router]);

  useEffect(() => {
    if (checked) return;
    authService.refresh()
      .then((s) => setSession(s.full_name, s.roles))
      .catch(() => clear());
  }, [checked, setSession, clear]);
}

export function useLogin() {
  const setSession = useSessionStore((s) => s.setSession);
  const toast = useUiStore((s) => s.toast);
  return useMutation({
    mutationFn: ({ emp, pin }: { emp: string; pin: string }) => authService.login(emp, pin),
    onSuccess: (s) => setSession(s.full_name, s.roles),
    onError: (e: ApiError) => toast(e.message, "danger"),
  });
}

export function useLogout() {
  const clear = useSessionStore((s) => s.clear);
  const router = useRouter();
  return useMutation({
    // R20 — phải gọi API, không chỉ đá về /login: phiên vẫn sống ở server.
    mutationFn: () => authService.logout(),
    onSettled: () => { clear(); router.replace("/login"); },
  });
}
