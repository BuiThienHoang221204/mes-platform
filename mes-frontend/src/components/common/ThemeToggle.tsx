"use client";

import { useUiStore } from "@/stores/useUiStore";

export function ThemeToggle() {
  const theme = useUiStore((s) => s.theme);
  const setTheme = useUiStore((s) => s.setTheme);

  return (
    <button
      type="button"
      onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
      aria-label="Đổi Sáng / Tối"
      className="min-h-[40px] whitespace-nowrap rounded-field px-2 text-body-sm text-fg-muted hover:bg-surface-2 hover:text-fg sm:px-3"
    >
      Sáng / Tối
    </button>
  );
}
