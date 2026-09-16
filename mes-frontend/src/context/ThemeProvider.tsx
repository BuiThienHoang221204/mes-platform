"use client";

import { useEffect, type ReactNode } from "react";
import { FONT_SCALE_STEPS, FS_DEFAULT, useUiStore } from "@/stores/useUiStore";

/**
 * Đổ lớp `.dark` và biến `--fs` ra thẻ <html>.
 *
 * Gắn lớp cho TỐI chứ không cho sáng — `globals.css` lấy sáng làm gốc, y roomify.
 *
 * Chế độ "system" phải NGHE `matchMedia` chứ không chỉ đọc một lần lúc mở app:
 * máy tính bảng để tự đổi sáng/tối theo giờ, đến chiều là lệch với giao diện.
 */
export function ThemeProvider({ children }: { children: ReactNode }) {
  const theme = useUiStore((s) => s.theme);
  const fontStep = useUiStore((s) => s.fontStep);

  useEffect(() => {
    const mq = window.matchMedia("(prefers-color-scheme: dark)");
    const apply = () =>
      document.documentElement.classList.toggle(
        "dark",
        theme === "dark" || (theme === "system" && mq.matches),
      );

    apply();
    if (theme !== "system") return;
    mq.addEventListener("change", apply);
    return () => mq.removeEventListener("change", apply);
  }, [theme]);

  useEffect(() => {
    const fs = FONT_SCALE_STEPS[fontStep] ?? FONT_SCALE_STEPS[FS_DEFAULT];
    document.documentElement.style.setProperty("--fs", String(fs));
  }, [fontStep]);

  return <>{children}</>;
}
