"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useForm } from "react-hook-form";

import { Eye, EyeClosed, Lock, SignIn, User } from "@/components/common/PhosphorIcons";
import { AppButton } from "@/components/ui/AppButton";
import { BrandMark } from "@/components/common/BrandMark";
import { AppInput } from "@/components/ui/AppInput";
import { useLogin } from "@/hooks/auth/useSession";
import { loginSchema, type LoginForm } from "@/schemas/auth";
import type { ApiError } from "@/types/api";

export default function LoginPage() {
  const router = useRouter();
  const login = useLogin();
  const [hienPin, setHienPin] = useState(false);

  const {
    register,
    handleSubmit,
    setValue,
    setError,
    formState: { errors },
  } = useForm<LoginForm>({
    resolver: zodResolver(loginSchema),
    defaultValues: { emp_code: "", pin: "" },
  });

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
    <main className="flex min-h-dvh flex-col items-center bg-bg px-5 pb-[calc(1.5rem+env(safe-area-inset-bottom))] pt-[calc(1.5rem+env(safe-area-inset-top))] sm:bg-surface-2 sm:px-4 sm:dark:bg-bg">
      <div className="my-auto w-full max-w-[26rem] sm:rounded-xl sm:border sm:border-line sm:bg-surface sm:p-8 sm:shadow-lg">
        <header className="text-center">
          <BrandMark className="mx-auto h-7 w-auto text-fg sm:h-8" />
          <h1 className="mt-6 text-h3 sm:text-h2">Đăng nhập</h1>
          <p className="mt-1 text-body-sm text-fg-muted">
            Mã nhân viên và mã PIN của riêng bạn
          </p>
        </header>

        <form onSubmit={submit} className="mt-7 space-y-5">
          <AppInput
            {...register("emp_code")}
            label="Mã nhân viên"
            placeholder="NV0142"
            autoFocus
            autoComplete="username"
            autoCapitalize="characters"
            mono
            leading={<User size={22} />}
            error={errors.emp_code?.message}
          />

          <AppInput
            {...register("pin")}
            label="Mã PIN"
            type={hienPin ? "text" : "password"}
            placeholder="••••"
            inputMode="numeric"
            autoComplete="current-password"
            maxLength={6}
            mono
            leading={<Lock size={22} />}
            trailing={
              <button
                type="button"
                onClick={() => setHienPin((v) => !v)}
                aria-label={hienPin ? "Ẩn mã PIN" : "Hiện mã PIN"}
                className="flex h-full w-11 items-center justify-center rounded-pill text-fg-subtle transition-colors hover:text-fg"
              >
                {hienPin ? <EyeClosed size={22} /> : <Eye size={22} />}
              </button>
            }
            error={errors.pin?.message}
          />

          <AppButton
            type="submit"
            variant="primary"
            shape="pill"
            block
            disabled={login.isPending}
            icon={<SignIn size={24} weight="bold" />}
          >
            {login.isPending ? "Đang vào…" : "Vào ca"}
          </AppButton>
        </form>

        <p className="mt-6 border-t border-line pt-5 text-center text-body-sm text-fg-subtle">
          Máy này ghi lại ai làm thao tác nào, nên hết ca nhớ bấm Đổi người.
        </p>
      </div>
    </main>
  );
}
