"use client";

import { use } from "react";

import { TraceDetail } from "@/components/mo/TraceDetail";

export default function TraceDetailPage({ params }: { params: Promise<{ code: string }> }) {
  const { code } = use(params);
  return <TraceDetail code={code} />;
}
