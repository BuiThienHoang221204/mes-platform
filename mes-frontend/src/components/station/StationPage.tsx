"use client";

import { useRouter, useSearchParams } from "next/navigation";
import type { ReactNode } from "react";

import { StepFlow } from "@/components/common/StepFlow";
import { StationHeader } from "@/components/station/StationHeader";
import { resolveStep } from "@/constants/stationSteps";
import { stationRoute } from "@/constants/stations";

type Props = {
  station: number;
  title: string;
  /** Mặc định ÉP trang vừa đúng một màn: nội dung dài thì cuộn BÊN TRONG thẻ.
   *  Tắt khi màn đó là một biểu mẫu dài, cuộn cả trang mới đúng. */
  fill?: boolean;
  children: (step: string) => ReactNode;
};

export function StationPage({ station, title, fill = true, children }: Props) {
  const params = useSearchParams();
  const router = useRouter();
  const step = resolveStep(station, params.get("step"));

  // Giữ nguyên mọi tham số khác khi đổi bước — trạm 4 mang `?mo=` để biết đang mở
  // lệnh nào, bấm sang bước khác mà mất nó thì người dùng phải chọn lại lệnh.
  const pick = (id: string) => {
    const next = new URLSearchParams(params.toString());
    if (id === resolveStep(station, null)) next.delete("step");
    else next.set("step", id);
    const qs = next.toString();
    router.replace(qs ? `${stationRoute(station)}?${qs}` : stationRoute(station));
  };

  return (
    <div className={fill ? "flex h-full min-h-0 flex-col" : ""}>
      <StationHeader station={station} title={title} />
      <div className={fill ? "flex min-h-0 flex-1 flex-col gap-5" : "space-y-5"}>
        <div className="shrink-0">
          <StepFlow station={station} active={step} onPick={pick} />
        </div>
        {children(step)}
      </div>
    </div>
  );
}
