"use client";

import type { ReactNode } from "react";

import { DeviceTablet, SignOut, User } from "@/components/common/PhosphorIcons";
import { FontScalePicker } from "@/components/settings/FontScalePicker";
import { SettingRow } from "@/components/settings/SettingRow";
import { ThemePicker } from "@/components/settings/ThemePicker";
import { AppButton } from "@/components/ui/AppButton";
import { roleLabel } from "@/constants/roles";
import { useLogout } from "@/hooks/auth/useSession";
import { useSessionStore } from "@/stores/useSessionStore";

function Panel({
  icon,
  title,
  hint,
  children,
}: {
  icon: ReactNode;
  title: string;
  hint: string;
  children: ReactNode;
}) {
  return (
    <section className="rounded-card border border-line bg-surface px-6 py-5">
      <header className="mb-2">
        <h2 className="flex items-center gap-2 text-title text-fg">
          <span className="text-accent">{icon}</span>
          {title}
        </h2>
        <p className="mt-1 text-body-sm text-fg-muted">{hint}</p>
      </header>
      {children}
    </section>
  );
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div className="min-w-48 flex-1">
      <div className="text-body-sm text-fg-subtle">{label}</div>
      <div className="mt-1 text-body-lg text-fg">{value}</div>
    </div>
  );
}

export default function AccountPage() {
  const fullName = useSessionStore((s) => s.fullName);
  const roles = useSessionStore((s) => s.roles);
  const logout = useLogout();

  return (
    <div className="mx-auto max-w-5xl space-y-5">
      <header className="space-y-1">
        <h1 className="text-h2">Tài khoản</h1>
        <p className="text-body text-fg-muted">Giao diện, cỡ chữ và phiên đăng nhập</p>
      </header>

      <Panel
        icon={<DeviceTablet size={22} />}
        title="Giao diện & hiển thị"
        hint="Áp cho toàn bộ ứng dụng, lưu trên máy này"
      >
        <SettingRow
          label="Giao diện"
          hint="Theo lựa chọn của bạn, hoặc chạy theo cài đặt Sáng/Tối của máy."
        >
          <ThemePicker />
        </SettingRow>

        <SettingRow
          label="Cỡ chữ"
          hint="Áp ngay cho mọi trang. Lưu riêng cho máy này — máy khác ở xưởng cần chỉnh lại."
        >
          <FontScalePicker />
        </SettingRow>
      </Panel>

      <Panel
        icon={<User size={22} />}
        title="Thông tin đăng nhập"
        hint="Lấy từ phiên hiện tại trên máy chủ"
      >
        <div className="flex flex-wrap gap-6 pb-5">
          <Field label="Họ và tên" value={fullName ?? "—"} />
          <Field label="Vai trò" value={roleLabel(roles)} />
        </div>
        <p className="border-t border-line pt-4 text-body-sm text-fg-muted">
          Chưa đổi được tên hay vai từ giao diện — hai thứ này do phòng nhân sự khai.
        </p>
      </Panel>

      <div className="flex flex-wrap items-center justify-between gap-4 px-2">
        <AppButton
          size="md"
          variant="danger"
          icon={<SignOut size={20} />}
          disabled={logout.isPending}
          onClick={() => logout.mutate()}
        >
          Đăng xuất khỏi thiết bị này
        </AppButton>
      </div>
    </div>
  );
}
