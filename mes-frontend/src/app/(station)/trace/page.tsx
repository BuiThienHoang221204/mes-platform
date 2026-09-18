"use client";

import { TraceLookup } from "@/components/mo/TraceLookup";

export default function TracePage() {
  return (
    <div className="space-y-5">
      <h1 className="text-h2">Truy cứu lệnh</h1>
      <TraceLookup />
    </div>
  );
}
