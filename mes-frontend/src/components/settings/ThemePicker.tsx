"use client";

import { Desktop, Moon, Sun } from "@/components/common/PhosphorIcons";
import { useUiStore, type ThemeMode } from "@/stores/useUiStore";

const MODES = [
  { id: "light", Icon: Sun, label: "Sáng" },
  { id: "dark", Icon: Moon, label: "Tối" },
  { id: "system", Icon: Desktop, label: "Tự động" },
] as const satisfies readonly { id: ThemeMode; Icon: typeof Sun; label: string }[];

export function ThemePicker() {
  const theme = useUiStore((s) => s.theme);
  const setTheme = useUiStore((s) => s.setTheme);

  return (
    <div
      role="radiogroup"
      aria-label="Giao diện"
      className="flex gap-1 rounded-pill bg-surface-2 p-1"
    >
      {MODES.map(({ id, Icon, label }) => {
        const on = theme === id;
        return (
          <button
            key={id}
            type="button"
            role="radio"
            aria-checked={on}
            onClick={() => setTheme(id)}
            className={`flex items-center gap-2 rounded-pill px-4 py-2 text-body-sm ${
              on ? "bg-surface font-semibold text-fg shadow-sm" : "text-fg-muted hover:text-fg"
            }`}
          >
            <Icon size={18} aria-hidden />
            {label}
          </button>
        );
      })}
    </div>
  );
}
