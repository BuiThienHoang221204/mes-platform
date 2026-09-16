import type { Config } from "tailwindcss";

/**
 * Thang chữ và weight chép nguyên từ roomify-ui (FE-PLAN §6.4).
 * Cỡ chữ KÈM LUÔN weight để không ai phải nhớ ghép đôi.
 */
const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  darkMode: "class",
  theme: {
    fontSize: {
      caption: ["var(--text-caption)", { fontWeight: "400" }],
      "body-sm": ["var(--text-body-sm)", { fontWeight: "400" }],
      body: ["var(--text-body)", { fontWeight: "400" }],
      "body-lg": ["var(--text-body-lg)", { fontWeight: "400" }],
      title: ["var(--text-title)", { fontWeight: "600" }],
      h3: ["var(--text-h3)", { fontWeight: "600" }],
      h2: ["var(--text-h2)", { fontWeight: "600" }],
      h1: ["var(--text-h1)", { fontWeight: "600" }],
      display: ["var(--text-display)", { fontWeight: "600" }],
      label: ["var(--text-label)", { fontWeight: "500" }],
      button: ["var(--text-button)", { fontWeight: "500" }],
      badge: ["var(--text-badge)", { fontWeight: "500" }],
    },
    extend: {
      fontFamily: { heading: ["var(--font-heading)"], sans: ["var(--font-sans)"], mono: ["var(--font-mono)"] },
      // R31 — cap ở 600. Gõ `font-bold` theo phản xạ vẫn ra 600, không phá được hệ.
      fontWeight: { normal: "400", medium: "500", semibold: "600", bold: "600", extrabold: "600", black: "600" },
      colors: {
        bg: "var(--color-bg)",
        surface: { DEFAULT: "var(--color-surface)", 2: "var(--color-surface-2)", 3: "var(--color-surface-3)" },
        line: { DEFAULT: "var(--color-line)", strong: "var(--color-line-strong)" },
        fg: { DEFAULT: "var(--color-fg)", muted: "var(--color-fg-muted)", subtle: "var(--color-fg-subtle)" },
        accent: {
          DEFAULT: "var(--color-accent)", on: "var(--color-accent-on)",
          soft: "var(--color-accent-soft)", strong: "var(--color-accent-strong)",
          line: "var(--color-accent-line)",
        },
        ok: { DEFAULT: "var(--color-ok)", on: "var(--color-ok-on)", soft: "var(--color-ok-soft)" },
        warn: { DEFAULT: "var(--color-warn)", on: "var(--color-warn-on)", soft: "var(--color-warn-soft)" },
        danger: { DEFAULT: "var(--color-danger)", on: "var(--color-danger-on)", soft: "var(--color-danger-soft)" },
        brand: "var(--color-brand)",
        overlay: "var(--color-overlay)",
      },
      // Đọc TỪ token, không gõ lại số: đổi bo góc ở `globals.css` là cả app theo.
      borderRadius: {
        xs: "var(--r-xs)", field: "var(--r-sm)", card: "var(--r-md)",
        lg: "var(--r-lg)", xl: "var(--r-xl)", pill: "var(--r-pill)",
      },
      boxShadow: {
        sm: "var(--shadow-sm)", DEFAULT: "var(--shadow-md)",
        md: "var(--shadow-md)", lg: "var(--shadow-lg)", soft: "var(--shadow-sm)",
      },
      minHeight: { touch: "56px" },   // §1 — vùng chạm tối thiểu ngoài xưởng
      spacing: { touch: "56px" },
    },
  },
  plugins: [],
};
export default config;
