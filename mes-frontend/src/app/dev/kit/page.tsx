"use client";

import { KitComponents } from "@/components/dev/KitComponents";
import { FontScalePicker } from "@/components/settings/FontScalePicker";
import { ThemePicker } from "@/components/settings/ThemePicker";

const SURFACES: [string, string][] = [
  ["bg", "bg-bg"],
  ["surface", "bg-surface"],
  ["surface-2", "bg-surface-2"],
  ["surface-3", "bg-surface-3"],
  ["line", "bg-line"],
  ["line-strong", "bg-line-strong"],
  ["fg", "bg-fg"],
  ["fg-muted", "bg-fg-muted"],
  ["fg-subtle", "bg-fg-subtle"],
];

const TONES: { name: string; solid: string; soft: string; outline: string }[] = [
  { name: "accent", solid: "bg-accent text-accent-on", soft: "bg-accent-soft text-accent", outline: "border-accent text-accent" },
  { name: "ok", solid: "bg-ok text-ok-on", soft: "bg-ok-soft text-ok", outline: "border-ok text-ok" },
  { name: "warn", solid: "bg-warn text-warn-on", soft: "bg-warn-soft text-warn", outline: "border-warn text-warn" },
  { name: "danger", solid: "bg-danger text-danger-on", soft: "bg-danger-soft text-danger", outline: "border-danger text-danger" },
];

const SIZES: [string, string][] = [
  ["display", "text-display"],
  ["h1", "text-h1"],
  ["h2", "text-h2"],
  ["h3", "text-h3"],
  ["title", "text-title"],
  ["body-lg", "text-body-lg"],
  ["body", "text-body"],
  ["body-sm", "text-body-sm"],
  ["caption", "text-caption"],
  ["label", "text-label"],
  ["button", "text-button"],
  ["badge", "text-badge"],
];

const RADII: [string, string][] = [
  ["field", "rounded-field"],
  ["card", "rounded-card"],
  ["pill", "rounded-pill"],
];

const ROWS: [string, number, number][] = [
  ["M068820", 10000, 8000],
  ["M068827", 2000, 1983],
  ["M068830", 900, 47],
];


function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="space-y-3">
      <h2 className="text-title">{title}</h2>
      {children}
    </section>
  );
}

export default function DevKit() {
  return (
    <main className="mx-auto max-w-5xl space-y-10 px-6 py-10">
      <header className="space-y-2">
        <h1 className="text-h1">Kiểm chứng token</h1>
        <p className="text-body text-fg-muted">
          Ô màu trong suốt = token thiếu. Chữ không đổi cỡ khi bấm nút = chỗ đó hardcode.
        </p>
      </header>

      <Section title="Điều khiển">
        <ThemePicker />
        <FontScalePicker />
      </Section>

      <Section title="Bộ component">
        <KitComponents />
      </Section>

      <Section title="Nền · viền · chữ">
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-5">
          {SURFACES.map(([name, cls]) => (
            <div key={name} className="space-y-1">
              <div className={`h-14 rounded-field border border-line ${cls}`} />
              <div className="text-caption text-fg-muted">{name}</div>
            </div>
          ))}
        </div>
      </Section>

      <Section title="Sắc thái — mỗi sắc ba biến thể">
        <div className="space-y-3">
          {TONES.map((t) => (
            <div key={t.name} className="flex flex-wrap items-center gap-3">
              <span className={`min-h-touch rounded-field px-5 py-3 text-button ${t.solid}`}>bg-{t.name}</span>
              <span className={`rounded-pill px-4 py-2 text-badge ${t.soft}`}>{t.name}-soft · chữ {t.name}</span>
              <span className={`rounded-field border px-4 py-2 text-body-sm ${t.outline}`}>viền {t.name}</span>
            </div>
          ))}
          <div className="rounded-field bg-brand px-4 py-2 text-body-sm text-brand-on">
            brand · vàng Amphenol — chỉ cho dấu hiệu thương hiệu, không dùng làm màu hành động
          </div>
        </div>
      </Section>

      <Section title="Thang chữ — bấm nút cỡ chữ ở trên, tất cả phải đổi">
        <div className="space-y-2">
          {SIZES.map(([name, cls]) => (
            <p key={name} className={cls}>
              <span className="text-fg-subtle">text-{name}</span> — Lệnh M068820 · Vỏ máy bơm A · đạt{" "}
              <span className="tnum">1.983</span>/<span className="tnum">2.000</span>
            </p>
          ))}
        </div>
      </Section>

      <Section title="Bo góc · vùng chạm · cột số">
        <div className="flex flex-wrap items-end gap-4">
          {RADII.map(([name, cls]) => (
            <div key={name} className={`flex min-h-touch min-w-touch items-center justify-center bg-surface-2 px-5 text-body-sm ${cls}`}>
              {name}
            </div>
          ))}
        </div>
        <table className="w-full border-collapse text-body-sm">
          <tbody>
            {ROWS.map(([code, a, b]) => (
              <tr key={code} className="border-b border-line">
                <td className="py-2 font-mono">{code}</td>
                <td className="py-2 text-right tnum">{a.toLocaleString("vi-VN")}</td>
                <td className="py-2 text-right tnum">{b.toLocaleString("vi-VN")}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <p className="text-caption text-fg-muted">
          R34 — cột số dùng <code className="font-mono">.tnum</code> để thẳng hàng, không đổi sang{" "}
          <code className="font-mono">font-mono</code>. Mã lệnh mới dùng mono.
        </p>
      </Section>
    </main>
  );
}
