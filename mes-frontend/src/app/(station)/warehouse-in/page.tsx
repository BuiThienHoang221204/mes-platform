"use client";

import { Suspense, useState } from "react";

import { FileMagnifyingGlass } from "@/components/common/PhosphorIcons";
import { QueueList } from "@/components/scan/QueueList";
import { AtStationTable } from "@/components/station/AtStationTable";
import { StationPage } from "@/components/station/StationPage";
import { StationScanArea } from "@/components/station/StationScanArea";
import { AppButton } from "@/components/ui/AppButton";
import { CompleteModal } from "@/components/warehouse-in/CompleteModal";
import { FULL } from "@/constants/roles";
import { useStationPerm } from "@/hooks/useStationPerm";
import type { AtStationRow } from "@/types/board";

const STATION = 5;

function WarehouseInBody() {
  const [picked, setPicked] = useState<AtStationRow | null>(null);
  const canWrite = useStationPerm(STATION) === FULL;

  return (
    <StationPage station={STATION} title="Nhập kho thành phẩm">
      {(step) => (
        <>
          {step === "scan" ? (
            <>
              <StationScanArea
                station={STATION}
                hint="Quét QR để Kho nhập nhận. Chỉ hiện lệnh Sản xuất đã đóng thùng xong."
              />
              <QueueList station={STATION} title="Hàng đợi Kho nhập" />
            </>
          ) : (
            <AtStationTable
              station={STATION}
              title="Đang giữ — chờ đối chiếu"
              action={(r) =>
                !canWrite ? null : (
                  <AppButton
                    size="md"
                    variant="primary"
                    onClick={() => setPicked(r)}
                    icon={<FileMagnifyingGlass size={24} />}
                  >
                    <span className="max-sm:hidden">Đối chiếu</span>
                  </AppButton>
                )
              }
            />
          )}
          <CompleteModal row={picked} onClose={() => setPicked(null)} />
        </>
      )}
    </StationPage>
  );
}

export default function WarehouseInPage() {
  return (
    <Suspense fallback={null}>
      <WarehouseInBody />
    </Suspense>
  );
}
