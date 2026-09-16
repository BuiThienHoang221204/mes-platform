import { getData } from "./http";
import type { AtStationRow, QueueRow, RunningRow, StationCounts } from "@/types/board";

export const boardService = {
  running: () => getData<RunningRow[]>("/board/running"),
  queue: (station: number) => getData<QueueRow[]>(`/board/queue/${station}`),
  atStation: (station: number) => getData<AtStationRow[]>(`/board/at/${station}`),
  counts: () => getData<StationCounts>("/board/counts"),
};
