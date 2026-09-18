"use client";

import { ArrowsClockwise, WarningCircle } from "@/components/common/PhosphorIcons";
import { AppButton } from "@/components/ui/AppButton";
import type { ApiError } from "@/types/api";

type Props = {
  error?: ApiError | Error | null;
  onRetry?: () => void;
  title?: string;
};

function messageOf(error?: ApiError | Error | null) {
  if (!error) return "Không tải được dữ liệu.";
  if ("message" in error && error.message) return error.message;
  return "Không tải được dữ liệu.";
}

function codeOf(error?: ApiError | Error | null) {
  return error && "code" in error ? (error as ApiError).code : null;
}

export function ErrorState({ error, onRetry, title = "Không tải được" }: Props) {
  const code = codeOf(error);
  return (
    <div className="flex flex-col items-center gap-3 px-6 py-12 text-center">
      <WarningCircle size={40} className="text-danger" />
      <p className="text-body-lg text-fg">{title}</p>
      <p className="max-w-md text-body text-fg-muted">{messageOf(error)}</p>
      {code ? <p className="font-mono text-caption text-fg-subtle">{code}</p> : null}
      {onRetry ? (
        <AppButton onClick={onRetry} icon={<ArrowsClockwise size={24} />}>
          Thử lại
        </AppButton>
      ) : null}
    </div>
  );
}
