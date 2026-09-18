import { create } from "zustand";
import { persist } from "zustand/middleware";

/** R29/R30 — 5 nấc cỡ chữ y như roomify. MES mặc định nấc 2 (1.15) vì đọc ngoài xưởng. */
export const FONT_SCALE_STEPS = [0.9, 1, 1.15, 1.3, 1.5] as const;
export const FONT_SCALE_LABELS = ["90%", "100%", "115%", "130%", "150%"] as const;
export const FS_DEFAULT = 2;

/** Ba chế độ, không phải hai — "system" đi theo cài đặt Sáng/Tối của máy. */
export type ThemeMode = "light" | "dark" | "system";

export type Toast = { id: number; text: string; kind: "ok" | "warn" | "danger" };

type UiState = {
  theme: ThemeMode;
  fontStep: number;
  navCollapsed: boolean;
  toasts: Toast[];
  setNavCollapsed: (v: boolean) => void;
  setTheme: (t: ThemeMode) => void;
  setFontStep: (n: number) => void;
  increaseFont: () => void;
  decreaseFont: () => void;
  toast: (text: string, kind?: Toast["kind"]) => void;
  dismiss: (id: number) => void;
};

let seq = 1;

export const useUiStore = create<UiState>()(
  persist(
    (set, get) => ({
      // Mặc định TỐI chứ không phải "system": màn này treo ở xưởng sáng chói cả ca,
      // mà máy tính bảng mới bóc hộp thì đang để chế độ sáng.
      theme: "dark",
      fontStep: FS_DEFAULT,
      navCollapsed: false,
      toasts: [],
      setNavCollapsed: (navCollapsed) => set({ navCollapsed }),
      setTheme: (theme) => set({ theme }),
      setFontStep: (n) =>
        set({ fontStep: Math.min(FONT_SCALE_STEPS.length - 1, Math.max(0, n)) }),
      increaseFont: () => get().setFontStep(get().fontStep + 1),
      decreaseFont: () => get().setFontStep(get().fontStep - 1),
      toast: (text, kind = "ok") => {
        // Bấm lại một thao tác đang lỗi thì chồng hai dải chữ y hệt nhau, che mất
        // đúng phần màn hình người ta cần đọc để sửa. Cùng câu đang hiện thì thôi.
        if (get().toasts.some((t) => t.text === text)) return;
        const id = seq++;
        set({ toasts: [...get().toasts, { id, text, kind }] });
        // Lỗi để lâu hơn báo thành công: người ở trạm đang đeo găng, đọc không kịp 3 giây.
        setTimeout(() => get().dismiss(id), kind === "ok" ? 3200 : 6000);
      },
      dismiss: (id) => set({ toasts: get().toasts.filter((t) => t.id !== id) }),
    }),
    {
      name: "mes-ui",
      partialize: (s) => ({ theme: s.theme, fontStep: s.fontStep, navCollapsed: s.navCollapsed }),
    },
  ),
);
