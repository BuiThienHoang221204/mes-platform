"use client";

import { useState } from "react";

import { BrandMark } from "@/components/common/BrandMark";
import {
  ChartBar,
  ClipboardText,
  ListNumbers,
  MagnifyingGlass,
  User,
  UserSwitch,
} from "@/components/common/PhosphorIcons";
import { NavGroup, type NavItem } from "@/components/common/SidebarNav";
import { RoleSwitchModal } from "@/components/dev/RoleSwitchModal";
import { AppButton } from "@/components/ui/AppButton";
import { PLANNER_ROUTE, PLANNER_STEPS } from "@/constants/plannerSteps";
import { REPORT_ROUTE, REPORT_STEPS } from "@/constants/reportSteps";
import { IS_DEV } from "@/constants/devAccounts";
import { PLANNER, roleLabel } from "@/constants/roles";
import { stepsOf } from "@/constants/stationSteps";
import { stationRoute } from "@/constants/stations";
import { useLogout } from "@/hooks/auth/useSession";
import { useCounts } from "@/hooks/board/useBoard";
import { useMyStation } from "@/hooks/useStationPerm";
import { useSessionStore } from "@/stores/useSessionStore";

/* Ô điều hướng ở `SidebarNav` cao 48px chứ không 56px như token `touch`.
   Vai điều độ có tới 11 mục — để 56px thì sidebar phải cuộn, mà cuộn ở đây tệ hơn
   thanh cuộn bình thường: mục bị khuất là mục không ai biết có tồn tại.

   48px vẫn trên ngưỡng vùng chạm của cả Apple (44) lẫn Material (48). Token `touch`
   giữ nguyên 56px cho NÚT BẤM — nút bấm nhầm thì ghi sai sổ, còn bấm nhầm mục điều
   hướng thì chỉ mất một lần bấm nữa. */
const stepHref = (route: string, id: string, first: boolean) =>
  first ? route : `${route}?step=${id}`;

const initials = (name: string) =>
  name.split(" ").slice(-2).map((w) => w[0]).join("").toUpperCase();

export function StationSidebar() {
  const fullName = useSessionStore((s) => s.fullName);
  const roles = useSessionStore((s) => s.roles);
  const logout = useLogout();
  const [swapOpen, setSwapOpen] = useState(false);
  const { data: counts } = useCounts();

  const isPlanner = roles.includes(PLANNER);
  const { station: mine } = useMyStation();
  const at = (n: number) => {
    if (!counts) return null;
    const k = String(n);
    return (counts.counts?.[k] ?? 0) + (counts.holding?.[k] ?? 0) || null;
  };

  const main: NavItem[] = isPlanner
    ? PLANNER_STEPS.map((s, i) => ({
        href: stepHref(PLANNER_ROUTE, s.id, i === 0),
        label: s.name,
        index: i + 1,
      }))
    : mine == null
      ? []
      : stepsOf(mine).map((s, i) => ({
          href: stepHref(stationRoute(mine), s.id, i === 0),
          label: s.name,
          index: i + 1,
          count: i === 0 ? at(mine) : null,
        }));

  const mainTitle = isPlanner
    ? "Điều độ"
    : mine == null
      ? "Trạm"
      : `Trạm của tôi · step ${mine}`;

  const reports: NavItem[] = REPORT_STEPS.map((s, i) => ({
    href: stepHref(REPORT_ROUTE, s.id, i === 0),
    label: s.name,
    index: i + 1,
  }));

  const shared: NavItem[] = [
    { href: "/running", label: "Bảng đang chạy", icon: <ChartBar size={22} /> },
    { href: "/flow", label: "Luồng toàn quy trình", icon: <ClipboardText size={22} /> },
    {
      href: REPORT_ROUTE,
      label: "Báo cáo sản xuất",
      icon: <ListNumbers size={22} />,
      children: reports,
    },
  ];

  const lookup: NavItem[] = [
    { href: "/trace", label: "Lịch sử & Truy cứu", icon: <MagnifyingGlass size={22} /> },
  ];

  const personal: NavItem[] = [
    { href: "/account", label: "Tài khoản", icon: <User size={22} /> },
  ];

  return (
    <aside className="flex h-full w-72 shrink-0 flex-col overflow-hidden border-r border-line bg-surface">
      <div className="space-y-2 flex justify-center border-b border-line px-4 py-8">
        <BrandMark className="h-7 w-auto text-fg text-center" />
        {/* <span className="block truncate text-caption text-fg-subtle">
          MES v2.3 · Điều hành sản xuất
        </span> */}
      </div>

      <nav className="no-scrollbar flex-1 space-y-5 overflow-y-auto px-4 py-4">
        <NavGroup title={mainTitle} items={main} />
        <NavGroup title="Xem chung" items={shared} />
        <NavGroup title="Tra cứu" items={lookup} />
        <NavGroup title="Cá nhân" items={personal} />
      </nav>

      <div className="shrink-0 space-y-2.5 border-t border-line px-4 py-4">
        <div className="flex items-center gap-3 rounded-card border border-line bg-surface-2 px-3 py-2.5">
          <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-card bg-accent-soft text-body-sm font-semibold text-accent">
            {fullName ? initials(fullName) : "—"}
          </span>
          <span className="min-w-0">
            <span className="block truncate text-body font-semibold text-fg">{fullName ?? "—"}</span>
            <span className="block truncate text-caption text-fg-muted">{roleLabel(roles)}</span>
          </span>
        </div>
        <AppButton
          size="md"
          block
          onClick={() => (IS_DEV ? setSwapOpen(true) : logout.mutate())}
          disabled={logout.isPending}
          icon={<UserSwitch size={22} />}
        >
          Đổi người
        </AppButton>

        {IS_DEV ? (
          <RoleSwitchModal
            open={swapOpen}
            onClose={() => setSwapOpen(false)}
            onLogout={() => {
              setSwapOpen(false);
              logout.mutate();
            }}
          />
        ) : null}
      </div>
    </aside>
  );
}
