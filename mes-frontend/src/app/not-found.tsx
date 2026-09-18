import Link from "next/link";

import { BrandMark } from "@/components/common/BrandMark";
import { ArrowLeft, MagnifyingGlass } from "@/components/common/PhosphorIcons";

const LINK =
  "flex min-h-touch items-center gap-3 rounded-card border border-line bg-surface px-4 text-left hover:border-line-strong";

export default function NotFound() {
  return (
    <main className="mx-auto flex min-h-dvh w-full max-w-md flex-col justify-center gap-6 px-4 pb-[calc(2rem+env(safe-area-inset-bottom))] pt-[calc(2rem+env(safe-area-inset-top))] sm:gap-8 sm:px-6 sm:py-10">
      <header className="text-center">
        <BrandMark className="mx-auto h-8 w-auto text-fg" />
        <p className="mt-8 text-display tnum text-fg-subtle">404</p>
        <h1 className="mt-1 text-h3 sm:text-h2">Không có màn hình này</h1>
        <p className="mt-2 text-body text-fg-muted">
          Đường dẫn bạn mở không thuộc hệ thống. Có thể lệnh đã bị huỷ, hoặc đường dẫn được chép
          thiếu một đoạn.
        </p>
      </header>

      <nav className="space-y-2">
        <Link href="/scan" className={LINK}>
          <ArrowLeft size={22} className="shrink-0 text-fg-subtle" />
          <span className="min-w-0">
            <span className="block text-body text-fg">Về trạm của tôi</span>
            <span className="block text-caption text-fg-subtle">nơi quét nhận lệnh</span>
          </span>
        </Link>

        <Link href="/trace" className={LINK}>
          <MagnifyingGlass size={22} className="shrink-0 text-fg-subtle" />
          <span className="min-w-0">
            <span className="block text-body text-fg">Tra cứu một lệnh</span>
            <span className="block text-caption text-fg-subtle">nhập hoặc quét mã lệnh</span>
          </span>
        </Link>
      </nav>

      <p className="text-center text-body-sm text-fg-subtle">
        Nếu bạn tới đây từ một đường dẫn ai đó gửi, báo lại cho người gửi kèm giờ xảy ra.
      </p>
    </main>
  );
}
