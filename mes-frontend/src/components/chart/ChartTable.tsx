import type { ReactNode } from "react";

import { DataTable, type Column } from "@/components/ui/DataTable";

type Props = {
  head: string[];
  rows: ReactNode[][];
  numCols?: number[];
};

export function ChartTable({ head, rows, numCols = [] }: Props) {
  const columns: Column[] = head.map((h, i) => ({
    label: h,
    right: numCols.includes(i),
    cellClassName: numCols.includes(i) ? "font-mono text-body-sm" : "text-body-sm",
  }));

  return (
    <DataTable
      columns={columns}
      rows={rows.map((r, i) => ({ key: String(i), cells: r }))}
      pad="sm"
    />
  );
}
