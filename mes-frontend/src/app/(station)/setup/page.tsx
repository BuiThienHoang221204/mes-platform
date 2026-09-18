"use client";

import { Suspense } from "react";

import { QueueList } from "@/components/scan/QueueList";
import { AtStationTable } from "@/components/station/AtStationTable";
import { StationPage } from "@/components/station/StationPage";
import { StationScanArea } from "@/components/station/StationScanArea";

const STATION = 1;

function SetupBody() {
  return (
    <StationPage station={STATION} title="Setup máy">
      {(step) => (
        <>
          {step === "scan" ? (
            <>
              <StationScanArea
                station={STATION}
                hint="Quét QR để Setup nhận. Chỉ nhận được lệnh Kho xuất đã bàn giao."
              />
              <QueueList station={STATION} title="Hàng đợi Setup" />
            </>
          ) : (
            <AtStationTable station={STATION} title="Đang canh máy" />
          )}
        </>
      )}
    </StationPage>
  );
}

export default function SetupPage() {
  return (
    <Suspense fallback={null}>
      <SetupBody />
    </Suspense>
  );
}
