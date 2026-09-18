import { getData } from "./http";
import { PAGE_SIZE } from "@/constants/pagination";
import type { Page } from "@/types/api";
import type { HourlyQuery, HourlyReport, MoProgressRow } from "@/types/reports";

export type MoProgressQuery = { status?: string; dateFrom?: string; dateTo?: string };

export const reportsService = {
  moProgress: (q: MoProgressQuery = {}, limit = PAGE_SIZE, offset = 0) =>
    getData<Page<MoProgressRow>>("/reports/mo-progress", {
      ...(q.status ? { status: q.status } : {}),
      ...(q.dateFrom ? { date_from: q.dateFrom } : {}),
      ...(q.dateTo ? { date_to: q.dateTo } : {}),
      limit,
      offset,
    }),

  hourly: ({ bucket, dateFrom, dateTo }: HourlyQuery) =>
    getData<HourlyReport>("/reports/hourly", {
      bucket,
      date_from: dateFrom,
      date_to: dateTo,
    }),
};
