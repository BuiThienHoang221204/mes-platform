import type { ReactNode } from "react";

import type { PillTone } from "@/constants/status";

/**
 * Dải ghi chú có sắc thái — trước đây viết tay ở hơn mười chỗ với class hơi khác
 * nhau mỗi nơi, nên cùng một loại thông báo lại trông không giống nhau giữa các
 * màn hình. Sắc thái dùng chung bảng với `StatusPill` để một lệnh "màu cảnh báo"
 * chỉ có một nghĩa trong cả ứng dụng.
 */
const TONE: Record<PillTone, string> = {
  accent: "border-accent-line bg-accent-soft text-accent",
  ok: "border-ok bg-ok-soft text-ok",
  warn: "border-warn bg-warn-soft text-warn",
  danger: "border-danger bg-danger-soft text-danger",
  flat: "border-line bg-surface-2 text-fg-muted",
};

type Props = {
  tone?: PillTone;
  className?: string;
  children: ReactNode;
};

export function Note({ tone = "flat", className = "", children }: Props) {
  return (
    <p className={`rounded-field border px-4 py-3 text-body-sm ${TONE[tone]} ${className}`}>
      {children}
    </p>
  );
}
