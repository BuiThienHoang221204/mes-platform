"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";

import { DEV_PIN, type DevAccount } from "@/constants/devAccounts";
import { authService } from "@/services/auth.service";
import { useSessionStore } from "@/stores/useSessionStore";
import { useStationStore } from "@/stores/useStationStore";
import { useUiStore } from "@/stores/useUiStore";
import type { ApiError } from "@/types/api";

export function useDevRole() {
  const qc = useQueryClient();
  const setSession = useSessionStore((s) => s.setSession);
  const setPicked = useStationStore((s) => s.setPicked);
  const toast = useUiStore((s) => s.toast);
  const router = useRouter();

  return useMutation({
    mutationFn: async (acc: DevAccount) => {
      setPicked(acc.station);
      return authService.login(acc.emp, DEV_PIN);
    },
    onSuccess: (s) => {
      setSession(s.full_name, s.roles);
      qc.clear();
      router.replace("/scan");
      toast(`Đang xem bằng ${s.full_name}`);
    },
    onError: (e: ApiError) => toast(e.message, "danger"),
  });
}
