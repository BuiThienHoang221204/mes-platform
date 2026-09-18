"use client";

import { useQuery } from "@tanstack/react-query";

import { reportKeys } from "@/constants/queryKeys";
import { reportsService, type MoProgressQuery } from "@/services/reports.service";
import type { HourlyQuery } from "@/types/reports";

/** Báo cáo là để ĐỌC, không phải màn treo tường — không `refetchInterval`.
 *
 *  Bảng đang chạy làm mới mỗi 10 giây vì có người đứng chờ việc. Ở đây người xem
 *  đang đọc một con số rồi nghĩ; kéo dữ liệu đổi dưới tay họ chỉ làm mất chỗ.
 *  Backend cũng đã có `read_cache` 5 giây nên gọi dồn cũng không xuống tới CSDL.
 */
const READ = { staleTime: 60_000 } as const;

/** Một TRANG tiến độ lệnh. `total` để biết còn trang sau không.
 *
 *  Màn này không tự làm mới theo nhịp nên chuyển trang an toàn — không có chuyện
 *  đang xem trang 3 thì bị kéo về trang 1 giữa chừng như ba màn bảng. */
export const useMoProgress = (query: MoProgressQuery = {}, offset = 0, limit = 9) => {
  const q = useQuery({
    queryKey: reportKeys.moProgress(query.status, query.dateFrom, query.dateTo, limit, offset),
    queryFn: () => reportsService.moProgress(query, limit, offset),
    ...READ,
  });
  return { ...q, items: q.data?.items ?? [], total: q.data?.total ?? 0, limit, offset };
};

export const useHourly = (q: HourlyQuery) =>
  useQuery({
    queryKey: reportKeys.hourly(q.bucket, q.dateFrom, q.dateTo),
    queryFn: () => reportsService.hourly(q),
    ...READ,
  });
