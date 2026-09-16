"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState, type ReactNode } from "react";

export function QueryProvider({ children }: { children: ReactNode }) {
  // useState để mỗi tab một client — tạo ở module scope là dùng chung giữa request khi SSR.
  const [client] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            // Xưởng mất wifi chốc lát là chuyện thường; thử lại một lần rồi báo.
            retry: 1,
            refetchOnWindowFocus: true,
            staleTime: 30_000,
          },
          mutations: { retry: 0 },
        },
      }),
  );
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}
