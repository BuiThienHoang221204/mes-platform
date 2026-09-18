"use client";

import { Suspense, useState } from "react";

import { SealCheck } from "@/components/common/PhosphorIcons";
import { QcDecideModal } from "@/components/qc/QcDecideModal";
import { QueueList } from "@/components/scan/QueueList";
import { AtStationTable } from "@/components/station/AtStationTable";
import { StationPage } from "@/components/station/StationPage";
import { StationScanArea } from "@/components/station/StationScanArea";
import { AppButton } from "@/components/ui/AppButton";
import { FULL } from "@/constants/roles";
import { useStationPerm } from "@/hooks/useStationPerm";

const STATION = 2;

function QcBody() {
  const [picked, setPicked] = useState<string | null>(null);
  const canWrite = useStationPerm(STATION) === FULL;

  return (
    <StationPage station={STATION} title="QC · kiểm hàng đầu">
      {(step) => (
        <>
          {step === "scan" ? (
            <>
              <StationScanArea
                station={STATION}
                hint="Quét QR để QC nhận — bước Setup tự đóng cùng lúc. Quét xong vẫn phải ra kết quả."
              />
              <QueueList station={STATION} title="Hàng đợi QC" />
            </>
          ) : (
            <AtStationTable
              station={STATION}
              title="QC đang giữ — chưa chuyển Bàn team leader"
              action={(r) => {
                if (!canWrite) return null;
                if (r.qc_result) {
                  return (
                    <AppButton
                      size="md"
                      variant="primary"
                      disabled
                      title={`Đã kết luận lúc ${r.qc_checked_at?.slice(11, 16) ?? "—"} — chờ Bàn team leader quét nhận`}
                      icon={<SealCheck size={24} weight="fill" />}
                    >
                      {r.qc_result === "PASS" ? "Đã đạt" : "Đã không đạt"}
                    </AppButton>
                  );
                }
                return (
                  <AppButton
                    size="md"
                    variant="primary"
                    onClick={() => setPicked(r.code)}
                    icon={<SealCheck size={24} />}
                  >
                    Ra kết quả
                  </AppButton>
                );
              }}
            />
          )}
          <QcDecideModal code={picked} onClose={() => setPicked(null)} />
        </>
      )}
    </StationPage>
  );
}

export default function QcPage() {
  return (
    <Suspense fallback={null}>
      <QcBody />
    </Suspense>
  );
}
