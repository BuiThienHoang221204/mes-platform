import { postData } from "./http";
import type { OkOut, SessionOut, StationTokenOut } from "@/types/api";

export const authService = {
  login: (emp_code: string, pin: string) => postData<SessionOut>("/auth/login", { emp_code, pin }),
  refresh: () => postData<SessionOut>("/auth/refresh"),
  logout: () => postData<OkOut>("/auth/logout"),
  /**
   * Token của THIẾT BỊ, không phải của người — xem FE-PLAN §7.3.
   *
   * Backend nhận `station` là QUERY PARAM chứ không phải body, và chỉ vai
   * PLANNER gọi được (`require_role(PLANNER)`). Gửi trong body thì 422.
   */
  stationToken: (station: number) =>
    postData<StationTokenOut>(`/auth/station-token?station=${station}`),
};
