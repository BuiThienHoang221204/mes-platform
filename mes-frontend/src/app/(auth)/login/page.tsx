"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";

import { PinPad } from "@/components/auth/PinPad";
import { SignIn } from "@/components/common/PhosphorIcons";
import { AppButton } from "@/components/ui/AppButton";
import { BrandMark } from "@/components/common/BrandMark";
import { AppInput } from "@/components/ui/AppInput";
import { useLogin } from "@/hooks/auth/useSession";
import { loginSchema, type LoginForm } from "@/schemas/auth";
import type { ApiError } from "@/types/api";

export default function LoginPage() {
  const router = useRouter();
  const login = useLogin();

  const {
    register,
    handleSubmit,
    setValue,
    setError,
    watch,
    formState: { errors },
  } = useForm<LoginForm>({
    resolver: zodResolver(loginSchema),
    defaultValues: { emp_code: "", pin: "" },
  });

  const pin = watch("pin");

  const submit = handleSubmit(({ emp_code, pin }) =>
    login.mutate(
      { emp: emp_code, pin },
      {
        onSuccess: () => router.replace("/scan"),
        onError: (e: ApiError) => {
          setValue("pin", "");
          setError("pin", { message: e.message });
        },
      },
    ),
  );

  return (
    <main className="mx-auto flex min-h-dvh w-full max-w-md flex-col justify-center gap-8 px-6 py-10">
      <header className="space-y-3 text-center">
        <BrandMark className="mx-auto h-7 w-auto text-fg" />
        <h1 className="text-h1">Đăng nhập</h1>
        <p className="text-body text-fg-muted">Mã nhân viên và mã PIN của riêng bạn</p>
      </header>

      <form onSubmit={submit} className="space-y-6">
        <AppInput
          {...register("emp_code")}
          label="Mã nhân viên"
          placeholder="NV0142"
          autoFocus
          autoComplete="username"
          autoCapitalize="characters"
          mono
          error={errors.emp_code?.message}
        />

        <div className="space-y-2">
          <span className="block text-label text-fg-muted">Mã PIN</span>
          <PinPad
            value={pin}
            onChange={(v) => setValue("pin", v, { shouldValidate: false })}
            disabled={login.isPending}
          />
          {errors.pin?.message ? (
            <p className="text-center text-body-sm text-danger">{errors.pin.message}</p>
          ) : null}
        </div>

        <AppButton
          type="submit"
          variant="primary"
          block
          disabled={login.isPending}
          icon={<SignIn size={28} weight="bold" />}
        >
          {login.isPending ? "Đang vào…" : "Vào ca"}
        </AppButton>
      </form>

      <p className="text-center text-body-sm text-fg-subtle">
        Máy này ghi lại ai làm thao tác nào, nên hết ca nhớ bấm Đổi người.
      </p>
    </main>
  );
}
