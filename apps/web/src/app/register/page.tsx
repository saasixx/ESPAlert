"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import Image from "next/image";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Loader2 } from "lucide-react";

import { useAuth } from "@/contexts/auth-context";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";

const registerSchema = z
  .object({
    email: z.string().email("Email inválido"),
    display_name: z.string().max(50, "Máximo 50 caracteres").optional().or(z.literal("")),
    password: z
      .string()
      .min(8, "Mínimo 8 caracteres")
      .regex(/[A-Z]/, "Debe tener al menos una mayúscula")
      .regex(/[a-z]/, "Debe tener al menos una minúscula")
      .regex(/[0-9]/, "Debe tener al menos un número"),
    confirm: z.string(),
  })
  .refine((d) => d.password === d.confirm, {
    path: ["confirm"],
    message: "Las contraseñas no coinciden",
  });

type RegisterForm = z.infer<typeof registerSchema>;

export default function RegisterPage() {
  const { register: authRegister } = useAuth();
  const router = useRouter();
  const [serverError, setServerError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<RegisterForm>({ resolver: zodResolver(registerSchema) });

  const onSubmit = async (data: RegisterForm) => {
    setServerError(null);
    try {
      await authRegister(data.email, data.password, data.display_name || undefined);
      router.push("/");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Error al registrarse";
      const match = msg.match(/"detail":"([^"]+)"/);
      setServerError(match ? match[1] : "No se pudo crear la cuenta. Inténtalo de nuevo.");
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4">
      <div className="w-full max-w-sm space-y-6">
        {/* Logo */}
        <div className="flex flex-col items-center gap-2">
          <Image
            src="/espalert-logo.svg"
            alt="ESPAlert"
            width={48}
            height={48}
            className="dark:invert"
          />
          <h1 className="text-2xl font-bold">ESPAlert</h1>
          <p className="text-sm text-muted-foreground">Alertas en tiempo real para España</p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Crear cuenta</CardTitle>
            <CardDescription>Recibe alertas personalizadas en tu zona</CardDescription>
          </CardHeader>

          <form onSubmit={handleSubmit(onSubmit)} noValidate>
            <CardContent className="space-y-4">
              {serverError && (
                <p className="text-sm text-destructive bg-destructive/10 rounded-md px-3 py-2">
                  {serverError}
                </p>
              )}

              <div className="space-y-1.5">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="tu@email.com"
                  autoComplete="email"
                  aria-invalid={!!errors.email}
                  {...register("email")}
                />
                {errors.email && (
                  <p className="text-xs text-destructive">{errors.email.message}</p>
                )}
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="display_name">
                  Nombre{" "}
                  <span className="text-muted-foreground font-normal">(opcional)</span>
                </Label>
                <Input
                  id="display_name"
                  type="text"
                  placeholder="Tu nombre"
                  autoComplete="name"
                  aria-invalid={!!errors.display_name}
                  {...register("display_name")}
                />
                {errors.display_name && (
                  <p className="text-xs text-destructive">{errors.display_name.message}</p>
                )}
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="password">Contraseña</Label>
                <Input
                  id="password"
                  type="password"
                  placeholder="••••••••"
                  autoComplete="new-password"
                  aria-invalid={!!errors.password}
                  {...register("password")}
                />
                {errors.password && (
                  <p className="text-xs text-destructive">{errors.password.message}</p>
                )}
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="confirm">Confirmar contraseña</Label>
                <Input
                  id="confirm"
                  type="password"
                  placeholder="••••••••"
                  autoComplete="new-password"
                  aria-invalid={!!errors.confirm}
                  {...register("confirm")}
                />
                {errors.confirm && (
                  <p className="text-xs text-destructive">{errors.confirm.message}</p>
                )}
              </div>
            </CardContent>

            <CardFooter className="flex flex-col gap-3">
              <Button type="submit" className="w-full" disabled={isSubmitting}>
                {isSubmitting && <Loader2 className="animate-spin" />}
                Crear cuenta
              </Button>
              <p className="text-sm text-muted-foreground text-center">
                ¿Ya tienes cuenta?{" "}
                <Link href="/login" className="text-primary hover:underline font-medium">
                  Inicia sesión
                </Link>
              </p>
              <Link href="/" className="text-xs text-muted-foreground hover:underline text-center">
                Continuar sin cuenta →
              </Link>
            </CardFooter>
          </form>
        </Card>
      </div>
    </div>
  );
}
