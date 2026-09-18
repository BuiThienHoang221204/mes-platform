"use client";

import { usePathname, useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";

import { BrandMark } from "@/components/common/BrandMark";
import {
  ChartBar,
  ClipboardText,
  ListNumbers,
  MagnifyingGlass,
  SidebarSimple,
  User,
  UserSwitch,
  X,
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

type Props = {
  open?: boolean;
  collapsed?: boolean;
  onClose?: () => void;
  onCollapse?: () => void;
  onExpand?: () => void;
};

const ICON_BTN =
  "flex h-11 w-11 items-center justify-center rounded-field text-fg-muted hover:bg-surface-2 hover:text-fg";

export function StationSidebar({
  open = false,
  collapsed = false,
  onClose,
  onCollapse,
  onExpand,
}: Props) {
  const fullName = useSessionStore((s) => s.fullName);
  const roles = useSessionStore((s) => s.roles);
  const logout = useLogout();
  const [swapOpen, setSwapOpen] = useState(false);
  const { data: counts } = useCounts();
  const pathname = usePathname();
  const params = useSearchParams();

  useEffect(() => {
    onClose?.();
  }, [pathname, params, onClose]);

  useEffect(() => {
    if (!open) return;
    const before = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = before;
    };
  }, [open]);

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
    <>
      <div
        aria-hidden
        onClick={onClose}
        className={`fixed inset-0 z-40 bg-overlay lg:hidden ${open ? "" : "hidden"}`}
      />

      <aside
        className={`fixed left-0 top-0 z-50 flex h-dvh w-72 max-w-[86vw] shrink-0 flex-col overflow-hidden border-r border-line bg-surface transition-[transform,width] duration-200 ease-out motion-reduce:transition-none lg:static lg:z-auto lg:h-full lg:max-w-none lg:translate-x-0 ${
          open ? "translate-x-0" : "-translate-x-full"
        } ${collapsed ? "lg:w-16" : ""}`}
      >
        {collapsed ? (
          <div className="fade-in hidden min-h-0 flex-1 flex-col lg:flex lg:w-16">
            <div className="flex shrink-0 justify-center border-b border-line py-5">
              <button
                type="button"
                onClick={onExpand}
                aria-label="Mở rộng thanh điều hướng"
                title="Mở rộng thanh điều hướng"
                className={ICON_BTN}
              >
                <SidebarSimple size={24} />
              </button>
            </div>

            <nav className="no-scrollbar min-h-0 flex-1 space-y-4 overflow-y-auto overscroll-contain py-4">
              <NavGroup rail title={mainTitle} items={main} />
              <NavGroup rail title="Xem chung" items={shared} />
              <NavGroup rail title="Tra cứu" items={lookup} />
              <NavGroup rail title="Cá nhân" items={personal} />
            </nav>

            <div className="mt-auto flex shrink-0 flex-col items-center gap-2 border-t border-line px-2 pb-[calc(1rem+env(safe-area-inset-bottom))] pt-4">
              <span
                title={`${fullName ?? "—"} · ${roleLabel(roles)}`}
                className="flex h-10 w-10 items-center justify-center rounded-card bg-accent-soft text-body-sm font-semibold text-accent"
              >
                {fullName ? initials(fullName) : "—"}
              </span>
              <button
                type="button"
                onClick={() => (IS_DEV ? setSwapOpen(true) : logout.mutate())}
                disabled={logout.isPending}
                aria-label="Đổi người"
                title="Đổi người"
                className={`${ICON_BTN} disabled:opacity-45`}
              >
                <UserSwitch size={22} />
              </button>
            </div>
          </div>
        ) : null}

        <div
          className={`relative flex shrink-0 items-center justify-center border-b border-line pb-5 pl-4 pr-14 pt-[calc(1.25rem+env(safe-area-inset-top))] lg:w-72 lg:pb-8 lg:pl-4 lg:pr-14 lg:pt-8 ${
            collapsed ? "lg:hidden" : ""
          }`}
        >
          <BrandMark className="h-7 w-auto text-center text-fg" />
          <button
            type="button"
            onClick={onClose}
            aria-label="Đóng điều hướng"
            className={`absolute right-2 ${ICON_BTN} lg:hidden`}
          >
            <X size={24} />
          </button>
          <button
            type="button"
            onClick={onCollapse}
            aria-label="Thu gọn thanh điều hướng"
            title="Thu gọn thanh điều hướng"
            className={`absolute right-2 hidden ${ICON_BTN} lg:flex`}
          >
            <SidebarSimple size={24} />
          </button>
        </div>

        <nav
          className={`no-scrollbar min-h-0 flex-1 space-y-5 overflow-y-auto overscroll-contain px-4 py-4 lg:w-72 ${
            collapsed ? "lg:hidden" : ""
          }`}
        >
          <NavGroup title={mainTitle} items={main} />
          <NavGroup title="Xem chung" items={shared} />
          <NavGroup title="Tra cứu" items={lookup} />
          <NavGroup title="Cá nhân" items={personal} />
        </nav>

        <div
          className={`mt-auto shrink-0 space-y-2.5 border-t border-line bg-surface px-4 pb-[calc(1rem+env(safe-area-inset-bottom))] pt-4 lg:w-72 ${
            collapsed ? "lg:hidden" : ""
          }`}
        >
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
    </>
  );
}
