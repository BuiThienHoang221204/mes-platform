"use client";

import { Suspense } from "react";

import { Printer, Truck } from "@/components/common/PhosphorIcons";
import { QueueList } from "@/components/scan/QueueList";
import { AtStationTable } from "@/components/station/AtStationTable";
import { StationPage } from "@/components/station/StationPage";
import { StationScanArea } from "@/components/station/StationScanArea";
import { AppButton } from "@/components/ui/AppButton";
import { AppCard } from "@/components/ui/AppCard";
import { QtyStat } from "@/components/ui/QtyStat";
import { FULL } from "@/constants/roles";
import { useAtStation, useQueue } from "@/hooks/board/useBoard";
import { useHandover, useHandoverBatch } from "@/hooks/station/useStationActions";
import { useStationPerm } from "@/hooks/useStationPerm";
import type { AtStationRow } from "@/types/board";

const STATION = 0;

function WarehouseOutBody() {
  const handover = useHandover();
  const batch = useHandoverBatch();
  const { items: at, total: atTotal } = useAtStation(STATION);
  const { items: queue, total: queueTotal } = useQueue(STATION);
  const canWrite = useStationPerm(STATION) === FULL;

  const pending = at.filter((r) => !r.handed_over_at);
  const handed = atTotal - pending.length;
  const rework = queue.filter((q) => q.round_no > 1).length;

  const rowAction = (r: AtStationRow) =>
    !canWrite ? null : r.handed_over_at ? (
      <span className="text-body-sm text-fg-subtle">đã bàn giao</span>
    ) : (
      <AppButton
        size="md"
        variant="primary"
        disabled={handover.isPending}
        onClick={() => handover.mutate(r.code)}
        icon={<Truck size={24} />}
      >
        Bàn giao
      </AppButton>
    );

  return (
    <StationPage station={STATION} title="Bàn giao vật tư xuống xưởng" fill>
      {(step) => (
        <div className="flex flex-col gap-4 lg:min-h-0 lg:flex-1 lg:gap-5">
          <div className="grid shrink-0 grid-cols-2 gap-2 sm:gap-3 lg:grid-cols-4">
            <QtyStat label="Chờ nhận" value={queueTotal} hint="lệnh mới + trả về" tone="accent" />
            <QtyStat label="Đã nhận, chưa giao" value={pending.length} hint="còn nằm ở kho" tone="warn" />
            <QtyStat label="Đã giao" value={handed} hint="xuống Setup" tone="ok" />
            <QtyStat label="Trong đó làm lại" value={rework} hint="QC trả về" tone="danger" />
          </div>

          {step === "scan" ? (
            <div className="flex flex-col gap-4 lg:min-h-0 lg:flex-1 lg:gap-5">
              <div className="shrink-0">
                <StationScanArea
                  station={STATION}
                  hint="Quét QR để Kho nhận lệnh. Nhận xong thì sang bước Bàn giao."
                />
              </div>
              <QueueList station={STATION} title="Hàng đợi Kho xuất" fill />
            </div>
          ) : null}

          {step === "handover" ? (
            <div className="flex flex-col gap-4 lg:min-h-0 lg:flex-1 lg:gap-5">
              <AtStationTable
                station={STATION}
                title="Đã nhận — chờ bàn giao xuống Setup"
                action={rowAction}
                fill
              />
              {canWrite && pending.length > 1 ? (
                <div className="flex flex-wrap items-center gap-3 rounded-card border border-line bg-surface px-4 py-4 sm:px-5">
                  <p className="w-full text-body-sm text-fg-muted sm:w-auto sm:min-w-0 sm:flex-1">
                    Phát lệnh đầu ca thì bàn giao cả lô — Kho phải xử được 10–100 lệnh một lúc.
                    Một mã hỏng thì cả lô không lệnh nào được bàn giao.
                  </p>
                  <AppButton
                    variant="primary"
                    className="w-full sm:w-auto"
                    disabled={batch.isPending}
                    onClick={() => batch.mutate(pending.map((r) => r.code))}
                    icon={<Truck size={28} weight="bold" />}
                  >
                    Bàn giao tất cả ({pending.length})
                  </AppButton>
                </div>
              ) : null}
            </div>
          ) : null}

          {step === "slip" ? (
            <AppCard
              title="Xem phiếu"
              meta={at.length ? `${at.length} lệnh · tra cứu, hệ thống không ghi sổ` : "tra cứu — hệ thống không ghi sổ"}
              className="flex flex-col lg:min-h-0 lg:flex-1"
              bodyClassName="flex flex-col gap-4 lg:min-h-0 lg:flex-1"
            >
              <p className="shrink-0 text-body text-fg-muted">
                Bước In phiếu đã bỏ khỏi quy trình: in hay không thì hàng vẫn xuống xưởng, và hệ
                thống vẫn chặn Setup nếu chưa bàn giao. Đây chỉ là tra cứu — bấm vào không ghi sổ,
                không có đồng hồ nào chạy.
              </p>
              {at.length ? (
                <div className="space-y-2 lg:min-h-0 lg:flex-1 lg:overflow-y-auto lg:pr-1">
                  {at.map((r) => (
                    <div
                      key={r.code}
                      className="flex flex-wrap items-center gap-2 rounded-field border border-line px-3 py-3 sm:gap-3 sm:px-4"
                    >
                      <span className="font-mono text-body-lg">{r.code}</span>
                      <span className="min-w-0 flex-1 truncate text-body text-fg-muted">
                        {r.product_name}
                      </span>
                      <AppButton
                        size="sm"
                        className="w-full sm:w-auto"
                        onClick={() => window.print()}
                        icon={<Printer size={20} />}
                      >
                        In bằng trình duyệt
                      </AppButton>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-body-sm text-fg-subtle">Chưa nhận lệnh nào để xem phiếu.</p>
              )}
            </AppCard>
          ) : null}
        </div>
      )}
    </StationPage>
  );
}

export default function WarehouseOutPage() {
  return (
    <Suspense fallback={null}>
      <WarehouseOutBody />
    </Suspense>
  );
}
