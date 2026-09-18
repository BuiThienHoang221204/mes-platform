"use client";

import { CheckCircle, SignOut } from "@/components/common/PhosphorIcons";
import { Note } from "@/components/ui/Note";
import { AppButton } from "@/components/ui/AppButton";
import { AppModal } from "@/components/ui/AppModal";
import { DEV_ACCOUNTS, DEV_PIN, DEV_PLANNER, type DevAccount } from "@/constants/devAccounts";
import { useDevRole } from "@/hooks/dev/useDevRole";
import { useSessionStore } from "@/stores/useSessionStore";

type Props = {
  open: boolean;
  onClose: () => void;
  onLogout: () => void;
};

function AccountCard({
  acc,
  active,
  busy,
  onPick,
}: {
  acc: DevAccount;
  active: boolean;
  busy: boolean;
  onPick: (a: DevAccount) => void;
}) {
  return (
    <button
      type="button"
      disabled={busy}
      onClick={() => onPick(acc)}
      className={`flex min-h-touch items-center gap-3 rounded-card border px-4 py-3 text-left disabled:opacity-45 ${
        active ? "border-accent bg-accent-soft" : "border-line bg-surface hover:border-line-strong"
      }`}
    >
      <span
        className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-card text-body-sm tnum ${
          active ? "bg-accent text-accent-on" : "bg-surface-2 text-fg-muted"
        }`}
      >
        {acc.station ?? "P"}
      </span>
      <span className="min-w-0">
        <span className={`block truncate text-body font-semibold ${active ? "text-accent" : "text-fg"}`}>
          {acc.dept} · {acc.level}
        </span>
        <span className="block truncate text-caption text-fg-muted">
          {acc.name} · <span className="font-mono">{acc.emp}</span>
        </span>
      </span>
      {active ? <CheckCircle size={22} weight="fill" className="ml-auto shrink-0 text-accent" /> : null}
    </button>
  );
}

export function RoleSwitchModal({ open, onClose, onLogout }: Props) {
  const fullName = useSessionStore((s) => s.fullName);
  const swap = useDevRole();

  const pick = (acc: DevAccount) => swap.mutate(acc, { onSuccess: onClose });

  return (
    <AppModal
      open={open}
      title="Đổi vai để xem màn hình khác"
      onClose={onClose}
      footer={
        <AppButton variant="danger" onClick={onLogout} icon={<SignOut size={22} />}>
          Đăng xuất hẳn
        </AppButton>
      }
    >
      <div className="space-y-5">
        <div className="space-y-2">
          <p className="text-caption uppercase tracking-wider text-fg-subtle">Theo phòng ban</p>
          <div className="grid gap-2 sm:grid-cols-2">
            {DEV_ACCOUNTS.map((a) => (
              <AccountCard
                key={a.emp}
                acc={a}
                active={fullName === a.name}
                busy={swap.isPending}
                onPick={pick}
              />
            ))}
          </div>
        </div>

        <div className="space-y-2">
          <p className="text-caption uppercase tracking-wider text-fg-subtle">Vai điều độ</p>
          <AccountCard
            acc={DEV_PLANNER}
            active={fullName === DEV_PLANNER.name}
            busy={swap.isPending}
            onPick={pick}
          />
        </div>

        <Note tone="warn">
          <strong>Chỉ có ở bản chạy thử.</strong> Bấm một vai là đăng nhập lại thật bằng tài khoản
          đó với mã PIN <span className="font-mono">{DEV_PIN}</span>, đồng thời gán luôn máy sang
          trạm của vai đó — nên ô quét dùng được ngay. Mọi thao tác vẫn ghi đúng tên người làm. Ở
          bản thật nút này biến mất, chỉ còn Đăng xuất.
        </Note>

        <p className="rounded-field border border-line bg-surface-2 px-4 py-3 text-body-sm text-fg-muted">
          Dữ liệu mẫu có <strong className="text-fg">8 tài khoản</strong>, không phải đủ 13 vai —
          hầu hết là Thành viên, riêng Sản xuất có cả Tổ trưởng. Hiện Tổ trưởng và Thành viên có
          quyền y hệt nhau; tách sẵn từ đầu vì sau này chắc chắn phải siết.
        </p>
      </div>
    </AppModal>
  );
}
