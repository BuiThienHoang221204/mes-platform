"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { Suspense } from "react";

import { RunningTable } from "@/components/board/RunningTable";
import { ProductionWorkspace } from "@/components/production/ProductionWorkspace";
import { QueueList } from "@/components/scan/QueueList";
import { AtStationTable } from "@/components/station/AtStationTable";
import { StationPage } from "@/components/station/StationPage";
import { StationScanArea } from "@/components/station/StationScanArea";
import { AppButton } from "@/components/ui/AppButton";
import { AppCard } from "@/components/ui/AppCard";
import { FULL } from "@/constants/roles";
import { useAtStation } from "@/hooks/board/useBoard";
import { useStationPerm } from "@/hooks/useStationPerm";

const STATION = 4;

/**
 * Thanh lệnh đang mở — thu gọn thay cho cả một bảng.
 *
 * Bảng lệnh đang giữ trước đây lặp lại trên MỌI tab của trạm 4, đẩy
 * phần việc thật xuống dưới 600px. Người vận hành làm một lệnh một lúc, nên chỉ
 * cần biết đang mở lệnh nào và đổi sang lệnh khác ở đâu.
 */
function PickedBar({ code, onChange }: { code: string; onChange: () => void }) {
  const { items, total } = useAtStation(STATION);
  const row = items.find((r) => r.code === code);
  const others = total - 1;

  return (
    <div className="flex flex-wrap items-center gap-4 rounded-card border border-line bg-surface px-5 py-3">
      <span className="font-mono text-body-lg text-fg">{code}</span>
      <span className="min-w-0 flex-1 truncate text-body text-fg-muted">
        {row?.product_name ?? "—"}
      </span>
      <AppButton size="sm" onClick={onChange}>
        Đổi lệnh{others > 0 ? ` (còn ${others})` : ""}
      </AppButton>
    </div>
  );
}

function ProductionBody() {
  const params = useSearchParams();
  const router = useRouter();
  const picked = params.get("mo");
  const canWrite = useStationPerm(STATION) === FULL;

  const open = (code: string) => router.replace(`/production?step=work&mo=${code}`);
  const clear = () => router.replace("/production?step=work");

  return (
    <StationPage station={STATION} title="Sản xuất · chuyền và đóng thùng">
      {(step) => (
        <>
          {step === "scan" ? (
            <>
              <StationScanArea
                station={STATION}
                hint="Quét QR để nhận lệnh vào Sản xuất. Nhận xong mới chia chuyền được."
              />
              <QueueList station={STATION} title="Hàng đợi Sản xuất" />
            </>
          ) : null}

          {step === "board" ? (
            <AppCard
              title="Bảng đang chạy"
              meta="một lệnh một dòng · tự làm mới 10 giây"
              flush
              className="flex min-h-0 flex-1 flex-col"
              bodyClassName="flex min-h-0 flex-1 flex-col"
            >
              <RunningTable withActions onlyAssigned fill />
            </AppCard>
          ) : null}

          {step === "work" ? (
            picked ? (
              <>
                <PickedBar code={picked} onChange={clear} />
                <ProductionWorkspace code={picked} />
              </>
            ) : (
              <AtStationTable
                station={STATION}
                title="Chọn lệnh để làm"
                action={(r) =>
                  !canWrite ? null : (
                    <AppButton size="md" variant="primary" onClick={() => open(r.code)}>
                      Mở bảng
                    </AppButton>
                  )
                }
              />
            )
          ) : null}
        </>
      )}
    </StationPage>
  );
}

export default function ProductionPage() {
  return (
    <Suspense fallback={null}>
      <ProductionBody />
    </Suspense>
  );
}
