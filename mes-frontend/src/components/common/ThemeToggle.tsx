"use client";

import { useUiStore } from "@/stores/useUiStore";

export function ThemeToggle() {
  const theme = useUiStore((s) => s.theme);
  const setTheme = useUiStore((s) => s.setTheme);

  return (
    <button
      type="button"
      onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
      className="min-h-[40px] rounded-field px-3 text-body-sm text-fg-muted hover:bg-surface-2 hover:text-fg"
    >
      Sáng / Tối
    </button>
  );
}
