"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useForm, Controller } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { ArrowLeft, Loader2, LogOut, User } from "lucide-react";

import { useAuth } from "@/contexts/auth-context";
import { apiFetch } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";

const settingsSchema = z.object({
  quiet_start: z.string().optional().or(z.literal("")),
  quiet_end: z.string().optional().or(z.literal("")),
  predictive_alerts: z.boolean(),
});

type SettingsForm = z.infer<typeof settingsSchema>;

export default function ProfilePage() {
  const { user, token, logout, refreshUser, isLoading } = useAuth();
  const router = useRouter();
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  // Redirect to login if not authenticated
  useEffect(() => {
    if (!isLoading && !user) {
      router.push("/login");
    }
  }, [isLoading, user, router]);

  const {
    register,
    handleSubmit,
    control,
    reset,
    formState: { isSubmitting, isDirty },
  } = useForm<SettingsForm>({
    resolver: zodResolver(settingsSchema),
    defaultValues: {
      quiet_start: "",
      quiet_end: "",
      predictive_alerts: true,
    },
  });

  // Populate form once user is loaded
  useEffect(() => {
    if (user) {
      reset({
        quiet_start: user.quiet_start ?? "",
        quiet_end: user.quiet_end ?? "",
        predictive_alerts: user.predictive_alerts,
      });
    }
  }, [user, reset]);

  const onSubmit = async (data: SettingsForm) => {
    setSaveError(null);
    setSaveSuccess(false);
    try {
      await apiFetch("/auth/me", {
        method: "PATCH",
        token: token ?? undefined,
        body: JSON.stringify({
          quiet_start: data.quiet_start || null,
          quiet_end: data.quiet_end || null,
          predictive_alerts: data.predictive_alerts,
        }),
      });
      await refreshUser();
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Error al guardar";
      setSaveError(msg);
    }
  };

  const handleLogout = () => {
    logout();
    router.push("/");
  };

  if (isLoading || !user) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="animate-spin text-muted-foreground" size={32} />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Topbar */}
      <header className="border-b bg-background/80 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-2xl mx-auto px-4 h-14 flex items-center gap-3">
          <Link href="/">
            <Button variant="ghost" size="icon-sm">
              <ArrowLeft />
            </Button>
          </Link>
          <h1 className="font-semibold">Mi perfil</h1>
        </div>
      </header>

      <main className="max-w-2xl mx-auto px-4 py-8 space-y-6">
        {/* User info */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-4">
              <div className="h-14 w-14 rounded-full bg-primary/10 flex items-center justify-center">
                <User size={28} className="text-primary" />
              </div>
              <div>
                <CardTitle className="text-xl">
                  {user.display_name ?? "Usuario"}
                </CardTitle>
                <CardDescription>{user.email}</CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <p className="text-xs text-muted-foreground">
              Cuenta creada el{" "}
              {new Date(user.created_at).toLocaleDateString("es-ES", {
                year: "numeric",
                month: "long",
                day: "numeric",
              })}
            </p>
          </CardContent>
        </Card>

        {/* Notification settings */}
        <Card>
          <CardHeader>
            <CardTitle>Preferencias de notificación</CardTitle>
            <CardDescription>
              Configura cómo y cuándo recibes alertas
            </CardDescription>
          </CardHeader>

          <form onSubmit={handleSubmit(onSubmit)}>
            <CardContent className="space-y-6">
              {/* Quiet hours */}
              <div className="space-y-3">
                <div>
                  <p className="text-sm font-medium">Horas de silencio</p>
                  <p className="text-xs text-muted-foreground mt-0.5">
                    No recibirás notificaciones en este intervalo (excepto alertas extremas)
                  </p>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-1.5">
                    <Label htmlFor="quiet_start">Inicio</Label>
                    <Input
                      id="quiet_start"
                      type="time"
                      {...register("quiet_start")}
                    />
                  </div>
                  <div className="space-y-1.5">
                    <Label htmlFor="quiet_end">Fin</Label>
                    <Input
                      id="quiet_end"
                      type="time"
                      {...register("quiet_end")}
                    />
                  </div>
                </div>
              </div>

              <Separator />

              {/* Predictive alerts */}
              <div className="flex items-center justify-between gap-4">
                <div>
                  <p className="text-sm font-medium">Alertas predictivas</p>
                  <p className="text-xs text-muted-foreground mt-0.5">
                    Aviso anticipado basado en tendencias meteorológicas e históricas
                  </p>
                </div>
                <Controller
                  name="predictive_alerts"
                  control={control}
                  render={({ field }) => (
                    <Switch
                      checked={field.value}
                      onCheckedChange={field.onChange}
                    />
                  )}
                />
              </div>

              {/* Feedback */}
              {saveSuccess && (
                <p className="text-sm text-green-600 dark:text-green-400 bg-green-500/10 rounded-md px-3 py-2">
                  Preferencias guardadas correctamente.
                </p>
              )}
              {saveError && (
                <p className="text-sm text-destructive bg-destructive/10 rounded-md px-3 py-2">
                  {saveError}
                </p>
              )}
            </CardContent>

            <div className="px-6 pb-6">
              <Button
                type="submit"
                disabled={isSubmitting || !isDirty}
                className="w-full"
              >
                {isSubmitting && <Loader2 className="animate-spin" />}
                Guardar cambios
              </Button>
            </div>
          </form>
        </Card>

        {/* Logout */}
        <Card>
          <CardContent className="pt-6">
            <Button
              variant="destructive"
              className="w-full"
              onClick={handleLogout}
            >
              <LogOut />
              Cerrar sesión
            </Button>
          </CardContent>
        </Card>
      </main>
    </div>
  );
}
