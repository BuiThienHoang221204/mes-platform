import { getData } from "./http";
import { PAGE_MAX, PAGE_SIZE } from "@/constants/pagination";
import type { Page } from "@/types/api";
import type { AtStationRow, QueueRow, RunningRow, StationCounts } from "@/types/board";

export const boardService = {
  running: (limit = PAGE_SIZE, offset = 0) =>
    getData<Page<RunningRow>>("/board/running", { limit, offset }),
  queue: (station: number, limit = PAGE_SIZE) =>
    getData<Page<QueueRow>>(`/board/queue/${station}`, { limit }),
  atStation: (station: number, limit = PAGE_MAX) =>
    getData<Page<AtStationRow>>(`/board/at/${station}`, { limit }),
  counts: (dateFrom?: string, dateTo?: string) =>
    getData<StationCounts>("/board/counts", {
      ...(dateFrom ? { date_from: dateFrom } : {}),
      ...(dateTo ? { date_to: dateTo } : {}),
    }),
};
