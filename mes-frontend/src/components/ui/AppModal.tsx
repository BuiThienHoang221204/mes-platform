"use client";

import { useEffect, type ReactNode } from "react";

import { X } from "@/components/common/PhosphorIcons";
import { AppButton } from "@/components/ui/AppButton";

type Props = {
  open: boolean;
  title: ReactNode;
  onClose: () => void;
  footer?: ReactNode;
  children: ReactNode;
};

export function AppModal({ open, title, onClose, footer, children }: Props) {
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      className="fixed inset-0 z-40 grid place-items-center bg-overlay p-4"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div className="flex max-h-[88dvh] w-full max-w-xl flex-col overflow-hidden rounded-card border border-line bg-surface shadow-lg">
        <header className="flex items-center gap-3 border-b border-line px-5 py-4">
          <h2 className="text-title">{title}</h2>
          <AppButton
            variant="ghost"
            size="sm"
            className="ml-auto"
            onClick={onClose}
            aria-label="Đóng"
          >
            <X size={24} />
          </AppButton>
        </header>

        <div className="no-scrollbar overflow-y-auto px-5 py-5">{children}</div>

        {footer ? (
          <footer className="flex flex-wrap justify-end gap-3 border-t border-line bg-surface-2 px-5 py-4">
            {footer}
          </footer>
        ) : null}
      </div>
    </div>
  );
}
