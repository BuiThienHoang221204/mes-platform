"use client";

import Link from "next/link";

import { ArrowRight, CaretRight, Lock, Warning } from "@/components/common/PhosphorIcons";
import { Note } from "@/components/ui/Note";
import { PageHeader } from "@/components/common/PageHeader";
import { AppCard } from "@/components/ui/AppCard";
import { flowOf } from "@/constants/flow";
import { permissionFor } from "@/constants/roles";
import { STATIONS } from "@/constants/stations";
import { useCounts } from "@/hooks/board/useBoard";
import { useStationPerm } from "@/hooks/useStationPerm";
import { useSessionStore } from "@/stores/useSessionStore";

/**
 * Một dòng của sáu trạm. Bấm được hay không tuỳ quyền XEM ở trạm đó.
 *
 * §12.4 — ngoài trạm của mình và trạm 4 thì không mở được màn hình trạm khác. Vẽ
 * dòng thành liên kết cho mọi người thì bấm vào là ăn 403: màn hình mời làm một
 * việc mà hệ thống sẽ từ chối, đúng loại lỗi khiến người vận hành hết tin nút bấm.
 *
 * Con SỐ thì vẫn hiện cho tất cả — §9b.5, cả xưởng cần biết đơn hàng đang tới đâu.
 * Cái bị giới hạn là mở màn hình thao tác của trạm, không phải bức tranh chung.
 */
function StationRow({ no, name, route }: { no: number; name: string; route: string }) {
  const counts = useCounts().data;
  const canOpen = useStationPerm(no) != null;
  const f = flowOf(no);

  // Mở được hay không phải NHÌN THẤY, không giấu trong chú thích khi rê chuột:
  // hai dòng trông y hệt nhau mà một dòng bấm được còn một dòng không thì người
  // dùng chỉ biết bằng cách thử.
  const body = (
    <>
      <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-pill bg-accent-soft text-body tnum text-accent">
        {no}
      </span>
      <span className="min-w-0 flex-1">
        <span className="block text-body-lg text-fg">{name}</span>
        <span className="block text-body-sm text-fg-muted">{f?.here}</span>
        {f?.back ? (
          <span className="mt-1 flex items-center gap-1.5 text-body-sm text-warn">
            <Warning size={16} weight="fill" />
            {f.back}
          </span>
        ) : null}
      </span>
      <span className="shrink-0 text-right">
        <span className="block text-body-lg tnum text-fg-muted">
          {counts?.counts?.[String(no)] ?? 0} chờ
        </span>
        <span
          className={`block text-body-sm tnum ${
            counts?.holding?.[String(no)] ? "text-accent" : "text-fg-subtle"
          }`}
        >
          {counts?.holding?.[String(no)] ?? 0} đang làm
        </span>
      </span>
      <span className="flex w-6 shrink-0 items-center justify-center">
        {canOpen ? (
          <CaretRight size={20} className="text-fg-subtle" />
        ) : (
          <Lock size={18} className="text-fg-subtle" />
        )}
      </span>
    </>
  );

  if (!canOpen) {
    return (
      <div
        className="flex cursor-not-allowed gap-4 px-5 py-4 opacity-60"
        title={`Bạn không thuộc phòng ban của ${name} — chỉ xem được con số`}
      >
        {body}
      </div>
    );
  }

  return (
    <Link href={route} className="flex gap-4 px-5 py-4 hover:bg-surface-2">
      {body}
    </Link>
  );
}

export default function FlowPage() {
  const roles = useSessionStore((s) => s.roles);
  // Đếm THẬT số trạm mở được thay vì hỏi "có phải điều độ không". Kho xuất mở được
  // hai trạm — trạm của họ và Sản xuất — nên ghi "chỉ xem" là nói sai với họ.
  const openable = STATIONS.filter((s) => permissionFor(roles, s.no) != null);

  return (
    <>
      <PageHeader
        kicker="Xem chung"
        title="Luồng toàn quy trình"
        subtitle="Lệnh đi qua sáu trạm theo thứ tự. Hai chỗ có ngã rẽ quay lui — đó cũng là hai chỗ người vận hành hay hoang mang nhất."
      />

      <div className="grid gap-5 lg:grid-cols-2">
        <AppCard
          title="Đường đi chính"
          meta={
            openable.length === STATIONS.length
              ? "sáu trạm · bấm để mở trạm nào cũng được"
              : openable.length
                ? `sáu trạm · bạn mở được ${openable.map((s) => s.name).join(" và ")}`
                : "sáu trạm · chỉ xem"
          }
          flush
        >
          <ul>
            {STATIONS.map((s) => (
              <li key={s.no} className="border-b border-line last:border-b-0">
                <StationRow no={s.no} name={s.name} route={s.route} />
              </li>
            ))}
          </ul>
        </AppCard>

        <div className="space-y-5">
          <AppCard title="Hai đường quay lui">
            <div className="space-y-3">
              <Note tone="warn">
                <strong>Thiếu số · chuyền dừng quá lâu → về Bàn team leader.</strong> Máy đã canh
                đúng, hàng đã qua QC, chỉ là chưa làm đủ. Không in lại phiếu, không canh máy lại,
                không kiểm lại.
              </Note>
              <Note tone="danger">
                <strong>QC không đạt → về Kho xuất.</strong> Không đạt nghĩa là canh máy sai nên
                phải làm lại từ gốc. Cho về Bàn team leader thì lệnh nhảy qua luôn Setup và QC —
                hàng lỗi đi thẳng vào chuyền mà không ai sửa máy.
              </Note>
            </div>
          </AppCard>

          <AppCard title="Hai quy ước xuyên suốt">
            <div className="space-y-3 text-body-sm text-fg-muted">
              <p className="flex gap-2">
                <ArrowRight size={18} className="mt-1 shrink-0" />
                <span>
                  <strong className="text-fg">Nhận bằng quét, không bấm Accept.</strong> Mã QR chỉ
                  nói lệnh nào; bước thì lấy từ máy đang đứng. Nên quét ở máy nào là nhận cho trạm đó.
                </span>
              </p>
              <p className="flex gap-2">
                <ArrowRight size={18} className="mt-1 shrink-0" />
                <span>
                  <strong className="text-fg">Bước trước đóng khi bước sau nhận.</strong> Setup và
                  Bàn team leader không có nút Hoàn thành — trạm sau quét là bước trước tự đóng.
                </span>
              </p>
            </div>
          </AppCard>
        </div>
      </div>
    </>
  );
}
