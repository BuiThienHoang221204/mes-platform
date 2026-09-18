"use client";

import { useEffect, useState, type ReactNode } from "react";
import { createPortal } from "react-dom";

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
  const [host, setHost] = useState<HTMLElement | null>(null);

  useEffect(() => setHost(document.body), []);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  if (!open || !host) return null;

  return createPortal(
    <div
      role="dialog"
      aria-modal="true"
      className="fixed inset-0 z-[60] grid items-end justify-items-stretch bg-overlay p-0 sm:place-items-center sm:p-4"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div className="flex max-h-[50dvh] w-full flex-col overflow-hidden rounded-t-lg border border-line bg-surface shadow-lg sm:max-h-[88dvh] sm:max-w-xl sm:rounded-card">
        <header className="flex items-center gap-3 border-b border-line px-4 py-2 sm:px-5 sm:py-3">
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

        <div className="no-scrollbar overflow-y-auto px-4 py-4 sm:px-5 sm:py-5">{children}</div>

        {footer ? (
          <footer className="flex flex-wrap justify-end gap-2 border-t border-line bg-surface-2 px-4 pb-[calc(0.75rem+env(safe-area-inset-bottom))] pt-3 sm:gap-3 sm:px-5 sm:py-4">
            {footer}
          </footer>
        ) : null}
      </div>
    </div>,
    host,
  );
}
