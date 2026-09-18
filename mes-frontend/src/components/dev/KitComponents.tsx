"use client";

import { useState } from "react";

import { Package, QrCode } from "@/components/common/PhosphorIcons";
import { AppButton } from "@/components/ui/AppButton";
import { AppCard } from "@/components/ui/AppCard";
import { AppInput } from "@/components/ui/AppInput";
import { AppModal } from "@/components/ui/AppModal";
import { AppSelect } from "@/components/ui/AppSelect";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { QtyStat } from "@/components/ui/QtyStat";
import { RoundBadge } from "@/components/ui/RoundBadge";
import { StationBadge } from "@/components/ui/StationBadge";
import { MoStatusPill, QcResultPill, SegmentPill, StatusPill } from "@/components/ui/StatusPill";
import { MO_FILTERS, MO_STATUS } from "@/constants/status";
import { STATIONS } from "@/constants/stations";

export function KitComponents() {
  const [open, setOpen] = useState(false);

  return (
    <div className="space-y-6">
      <AppCard title="Nút" meta="mọi size ≥ 56px trừ md/sm">
        <div className="flex flex-wrap items-center gap-3">
          <AppButton variant="primary" icon={<QrCode size={28} weight="bold" />}>
            Nhận lệnh
          </AppButton>
          <AppButton variant="outline">Bàn giao</AppButton>
          <AppButton variant="danger">Không đạt</AppButton>
          <AppButton variant="ghost">Bỏ qua</AppButton>
          <AppButton variant="primary" disabled>
            Đang gửi…
          </AppButton>
          <AppButton size="md">size md</AppButton>
          <AppButton size="sm">size sm</AppButton>
        </div>
      </AppCard>

      <AppCard title="Ô nhập">
        <div className="grid gap-4 sm:grid-cols-2">
          <AppInput label="Mã lệnh" placeholder="M068820" mono defaultValue="M068820" />
          <AppInput label="Số lượng" type="number" defaultValue={10000} hint="Đơn vị PCS" />
          <AppInput label="Mã sai" defaultValue="M06882" error="Mã phải là M + đúng 6 chữ số" />
          <AppSelect
            label="Trạm"
            options={STATIONS.map((s) => ({ value: s.no, label: `${s.no} · ${s.name}` }))}
            defaultValue={2}
          />
        </div>
      </AppCard>

      <AppCard title="Trạng thái">
        <div className="space-y-4">
          <div className="flex flex-wrap items-center gap-2">
            {MO_FILTERS.map((s) => (
              <MoStatusPill key={s} status={s} />
            ))}
            <MoStatusPill status={MO_STATUS.SUBMITTED} />
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <QcResultPill result="PASS" />
            <QcResultPill result="FAIL" />
            <SegmentPill kind="WAIT" />
            <SegmentPill kind="RUN" />
            <StatusPill tone="warn">Rework</StatusPill>
            <StatusPill tone="danger" live>
              Đang dừng L06
            </StatusPill>
          </div>
          <div className="flex flex-wrap items-center gap-4">
            {STATIONS.slice(0, 3).map((s) => (
              <StationBadge key={s.no} station={s.no} />
            ))}
            <StationBadge station={4} size="sm" muted />
          </div>
          <div className="flex flex-wrap items-center gap-4">
            <RoundBadge round={1} />
            <RoundBadge round={2} target={2000} quantity={10000} />
            <RoundBadge round={3} target={600} quantity={9000} />
          </div>
        </div>
      </AppCard>

      <AppCard title="Con số">
        <div className="grid gap-3 sm:grid-cols-4">
          <QtyStat label="SL đạt" value={1983} unit="pcs" tone="ok" />
          <QtyStat label="SL hỏng" value={12} unit="pcs" tone="danger" hint="Lỗi ép nhựa" />
          <QtyStat label="SL thiếu" value={5} unit="pcs" tone="warn" hint="Hết ca" />
          <QtyStat label="Đã đóng thùng" value={1800} unit="pcs" tone="accent" hint="9 thùng × 200" />
        </div>
      </AppCard>

      <div className="grid gap-4 sm:grid-cols-2">
        <AppCard title="Rỗng" flush>
          <EmptyState
            icon={<Package size={40} />}
            title="Hàng đợi trống"
            hint="Chưa có lệnh nào chờ ở trạm này."
          />
        </AppCard>
        <AppCard title="Lỗi" flush>
          <ErrorState
            error={{ code: "NO_HANDOVER", message: "Kho chưa bàn giao lệnh này xuống xưởng.", status: 409 }}
            onRetry={() => undefined}
          />
        </AppCard>
      </div>

      <AppCard title="Hộp thoại">
        <AppButton onClick={() => setOpen(true)}>Mở hộp thoại</AppButton>
        <AppModal
          open={open}
          title="Xác nhận bàn giao"
          onClose={() => setOpen(false)}
          footer={
            <>
              <AppButton variant="ghost" onClick={() => setOpen(false)}>
                Huỷ
              </AppButton>
              <AppButton variant="primary" onClick={() => setOpen(false)}>
                Bàn giao
              </AppButton>
            </>
          }
        >
          <p className="text-body text-fg-muted">
            Bàn giao 3 lệnh xuống Setup. Bấm Esc hoặc ra ngoài để đóng.
          </p>
        </AppModal>
      </AppCard>
    </div>
  );
}
