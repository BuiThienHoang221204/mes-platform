"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";

import { AppButton } from "@/components/ui/AppButton";
import { AppInput } from "@/components/ui/AppInput";
import { AppSelect } from "@/components/ui/AppSelect";
import { useMoActions } from "@/hooks/mo/useMo";
import { moCreateSchema, type MoCreateForm as Form } from "@/schemas/mo";
import { orZero } from "@/schemas/zodSetup";
import type { ApiError } from "@/types/api";

export function MoSingleForm() {
  const { create } = useMoActions();
  const {
    register,
    handleSubmit,
    setError,
    reset,
    formState: { errors },
  } = useForm<Form>({ resolver: zodResolver(moCreateSchema) });

  // Quy cách bỏ trống = 0 = mặt hàng không đóng thùng. Hai ô còn lại schema đã
  // bắt buộc phải có số nên tới đây chắc chắn là số thật.
  const submit = handleSubmit((v) =>
    create.mutate({ ...v, pcs_per_box: orZero(v.pcs_per_box) }, {
      onSuccess: () => reset(),
      onError: (e: unknown) => setError("code", { message: (e as ApiError).message }),
    }),
  );

  return (
    <form onSubmit={submit} className="space-y-4">
      <div className="grid gap-4 sm:grid-cols-2">
        <AppInput
          label="Mã lệnh"
          mono
          placeholder="M068831"
          hint="chữ M kèm đúng 6 chữ số"
          error={errors.code?.message}
          {...register("code")}
        />
        <AppInput
          label="Tên con hàng"
          placeholder="Vỏ hộp số M"
          error={errors.product_name?.message}
          {...register("product_name")}
        />
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <AppInput
          label="Số lượng"
          type="number"
          inputMode="numeric"
          error={errors.quantity?.message}
          {...register("quantity", { valueAsNumber: true })}
        />
        <AppSelect label="Đơn vị" options={[{ value: "PCS", label: "PCS" }]} defaultValue="PCS" />
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <AppInput
          label="Quy cách (pcs/thùng)"
          type="number"
          inputMode="numeric"
          hint="0 = không đóng thùng"
          error={errors.pcs_per_box?.message}
          {...register("pcs_per_box", { valueAsNumber: true })}
        />
        <AppInput
          label="Thời gian yêu cầu (phút)"
          type="number"
          inputMode="numeric"
          hint="chỉ áp dụng cho bước Sản xuất"
          error={errors.required_production_min?.message}
          {...register("required_production_min", { valueAsNumber: true })}
        />
      </div>

      <AppButton type="submit" variant="primary" disabled={create.isPending}>
        Tạo lệnh nháp
      </AppButton>
    </form>
  );
}
