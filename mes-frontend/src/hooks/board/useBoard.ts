"use client";

import { useQuery } from "@tanstack/react-query";
import { boardKeys } from "@/constants/queryKeys";
import { boardService } from "@/services/board.service";

/** R4/R5 — bảng sống thì `refetchInterval`, KHÔNG `setInterval` thủ công. */
const SONG = { staleTime: 0, refetchInterval: 10_000 } as const;

export const useQueue = (station: number | null) =>
  useQuery({
    queryKey: boardKeys.queue(station ?? -1),
    queryFn: () => boardService.queue(station as number),
    enabled: station !== null,
    ...SONG,
  });

/** Lệnh đang nằm trong tay trạm — quét xong thì nó rơi vào đây, không biến mất. */
export const useAtStation = (station: number | null) =>
  useQuery({
    queryKey: boardKeys.atStation(station ?? -1),
    queryFn: () => boardService.atStation(station as number),
    enabled: station !== null,
    ...SONG,
  });

export const useCounts = () =>
  useQuery({ queryKey: boardKeys.counts(), queryFn: boardService.counts, ...SONG });

export const useRunning = () =>
  useQuery({ queryKey: boardKeys.running(), queryFn: boardService.running, ...SONG });
