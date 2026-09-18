"use client";

import { Plus, UploadSimple } from "@/components/common/PhosphorIcons";
import { MoExcelImport } from "@/components/mo/MoExcelImport";
import { MoSingleForm } from "@/components/mo/MoSingleForm";
import { Tabs } from "@/components/ui/Tabs";

export function MoCreateForm() {
  return (
    <Tabs
      tabs={[
        {
          id: "single",
          label: "Tạo lẻ",
          meta: "một lệnh, trạng thái Nháp",
          icon: <Plus size={20} />,
          panel: <MoSingleForm />,
        },
        {
          id: "excel",
          label: "Nhập từ Excel",
          meta: "5 cột A–E, lấy theo vị trí cột",
          icon: <UploadSimple size={20} />,
          panel: <MoExcelImport />,
        },
      ]}
    />
  );
}
