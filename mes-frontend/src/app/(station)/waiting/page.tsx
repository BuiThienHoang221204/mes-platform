"use client";

import { Suspense } from "react";

import { Factory } from "@/components/common/PhosphorIcons";
import { QueueList } from "@/components/scan/QueueList";
import { AtStationTable } from "@/components/station/AtStationTable";
import { StationPage } from "@/components/station/StationPage";
import { StationScanArea } from "@/components/station/StationScanArea";
import { AppButton } from "@/components/ui/AppButton";

const STATION = 3;

function WaitingBody() {
  return (
    <StationPage station={STATION} title="Bàn team leader">
      {(step) => (
        <>
          {step === "scan" ? (
            <>
              <StationScanArea
                station={STATION}
                hint="Quét QR để nhận lệnh vào bàn chờ. Lệnh thiếu số từ Kho nhập cũng quay về đây."
              />
              <QueueList station={STATION} title="Hàng đợi Bàn team leader" />
            </>
          ) : (
            <AtStationTable
              station={STATION}
              title="Đang giữ — chờ chia chuyền"
              action={() => (
                <AppButton
                  size="md"
                  variant="primary"
                  compact
                  aria-label="Sang Sản xuất"
                  icon={<Factory size={24} />}
                >
                  <a href="/production">Sang Sản xuất</a>
                </AppButton>
              )}
            />
          )}
        </>
      )}
    </StationPage>
  );
}

export default function WaitingPage() {
  return (
    <Suspense fallback={null}>
      <WaitingBody />
    </Suspense>
  );
}
