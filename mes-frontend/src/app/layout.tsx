import type { Metadata, Viewport } from "next";

import { IconProvider } from "@/components/common/PhosphorIcons";
import { QueryProvider } from "@/context/QueryProvider";
import { ThemeProvider } from "@/context/ThemeProvider";
import { ToastHost } from "@/context/ToastProvider";

import "./globals.css";

export const metadata: Metadata = {
  title: "MES — Điều hành sản xuất",
  description: "Hệ điều hành sản xuất — quét QR, theo dõi chuyền, chốt sổ từng vòng.",
  manifest: "/manifest.json",
  // R27 — iOS BỎ QUA manifest.json. Icon màn hình chính của iPad chỉ lấy từ thẻ này.
  appleWebApp: { capable: true, statusBarStyle: "black-translucent", title: "MES" },
  icons: {
    icon: [{ url: "/icon-192x192.png", sizes: "192x192", type: "image/png" }],
    apple: [{ url: "/apple-touch-icon.png" }],
  },
};

export const viewport: Viewport = {
  themeColor: "#0D0F12",
  width: "device-width",
  initialScale: 1,
  // Để env(safe-area-inset-*) có giá trị khi chạy display:standalone (R33, .pt-safe).
  viewportFit: "cover",
};

/**
 * R32 — Script chống FOUC. Luật sáng/tối ở đây phải khớp TỪNG CHỮ với
 * `ThemeProvider.tsx`; lệch một chỗ là app nháy đúng một nhịp mỗi lần mở, và chỉ
 * với người để chế độ `system` — loại lỗi không ai báo mà ai cũng thấy.
 *
 * Ba thứ phải giống nhau giữa hai nơi:
 *   khoá localStorage  'mes-ui'          ← useUiStore persist name
 *   mặc định theme     'dark'            ← useUiStore initial state
 *   nấc cỡ chữ         [.9,1,1.15,1.3,1.5], mặc định nấc 2  ← FONT_SCALE_STEPS/FS_DEFAULT
 *
 * Chạy đồng bộ trong <head> để lớp `.dark` có mặt TRƯỚC lần vẽ đầu tiên.
 */
const FOUC_GUARD = `(function(){try{
var s=(JSON.parse(localStorage.getItem('mes-ui')||'{}').state)||{};
var t=s.theme||'dark';
var st=[0.9,1,1.15,1.3,1.5];
var fs=st[s.fontStep]!=null?st[s.fontStep]:st[2];
var m=window.matchMedia('(prefers-color-scheme: dark)').matches;
var d=document.documentElement;
d.classList.toggle('dark',t==='dark'||(t==='system'&&m));
d.style.setProperty('--fs',String(fs));
}catch(e){document.documentElement.classList.add('dark');}})();`;

/** R24 — service worker viết tay. Đăng ký sau `load` để không tranh băng thông
 *  với lần vẽ đầu. Hỏng thì bỏ qua: PWA là tiện nghi, không phải điều kiện chạy. */
const SW_REGISTER = `if('serviceWorker' in navigator){
window.addEventListener('load',function(){navigator.serviceWorker.register('/sw.js').catch(function(){});});
}`;

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    // suppressHydrationWarning: script trên cố ý sửa class/style của <html> trước khi React gắn vào.
    <html lang="vi" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: FOUC_GUARD }} />
      </head>
      <body className="min-h-dvh bg-bg text-fg antialiased">
        <QueryProvider>
          <ThemeProvider>
            <IconProvider>
              {children}
              <ToastHost />
            </IconProvider>
          </ThemeProvider>
        </QueryProvider>
        <script dangerouslySetInnerHTML={{ __html: SW_REGISTER }} />
      </body>
    </html>
  );
}
