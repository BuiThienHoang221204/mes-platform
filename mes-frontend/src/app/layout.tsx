import type { Metadata, Viewport } from "next";

import { IconProvider } from "@/components/common/PhosphorIcons";
import { SessionBoot } from "@/components/common/SessionBoot";
import { QueryProvider } from "@/context/QueryProvider";
import { ThemeProvider } from "@/context/ThemeProvider";
import { ToastHost } from "@/context/ToastProvider";

import "./globals.css";

export const metadata: Metadata = {
  title: "MES | Amphenol RF",
  description: "Hệ điều hành sản xuất — quét QR, theo dõi chuyền, chốt sổ từng vòng.",
  manifest: "/manifest.json",
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
  viewportFit: "cover",
};

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

const SW_REGISTER = `if('serviceWorker' in navigator){
window.addEventListener('load',function(){navigator.serviceWorker.register('/sw.js').catch(function(){});});
}`;

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="vi" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: FOUC_GUARD }} />
      </head>
      <body className="min-h-dvh bg-bg text-fg antialiased">
        <QueryProvider>
          <ThemeProvider>
            <IconProvider>
              <SessionBoot>{children}</SessionBoot>
              <ToastHost />
            </IconProvider>
          </ThemeProvider>
        </QueryProvider>
        <script dangerouslySetInnerHTML={{ __html: SW_REGISTER }} />
      </body>
    </html>
  );
}
