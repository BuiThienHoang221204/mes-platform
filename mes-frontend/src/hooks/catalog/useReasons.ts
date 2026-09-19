"use client";

import { useQuery } from "@tanstack/react-query";

import { catalogKeys } from "@/constants/queryKeys";
import type { ReasonGroupValue } from "@/constants/reasons";
import { catalogService } from "@/services/catalog.service";

export const useReasons = (group: ReasonGroupValue | undefined, enabled = true) =>
  useQuery({
    queryKey: catalogKeys.reasons(group),
    queryFn: () => catalogService.reasons(group),
    staleTime: Infinity,
    enabled,
  });
