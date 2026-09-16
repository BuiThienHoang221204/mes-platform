"use client";

import { useMutation } from "@tanstack/react-query";
import { authService } from "@/services/auth.service";
import { stationName } from "@/constants/stations";
import { useStationStore } from "@/stores/useStationStore";
import { useUiStore } from "@/stores/useUiStore";
import type { ApiError } from "@/types/api";

/**
 * Xin token trạm mới cho CHÍNH máy này, không rời màn đang mở.
 *
 * Backend đã chặn đúng chỗ: `/auth/station-token` là `require_role(PLANNER)`, nên
 * hàm này không mở thêm quyền gì — nó chỉ bỏ bớt mấy lần bấm cho người vốn đã có
 * quyền. Điều độ đi thử hết luồng trên một máy là việc có thật: chạy thử, đào tạo,
 * và gỡ rối khi một trạm kẹt.
 *
 * Vẫn phải BẤM, không tự đổi: máy ở xưởng là máy của trạm đó: tự đổi token ngầm
 * thì ca sau có người quét vào nhầm trạm mà không ai biết vì sao.
 */
export function useStationSwitch() {
  const setStation = useStationStore((s) => s.setStation);
  const toast = useUiStore((s) => s.toast);

  return useMutation({
    mutationFn: (station: number) => authService.stationToken(station),
    onSuccess: (r) => {
      setStation(r.station, r.token);
      toast(`Máy này giờ là ${stationName(r.station)}`);
    },
    onError: (e: ApiError) => toast(e.message, "danger"),
  });
}
