import { notFound } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, ExternalLink, MapPin, Activity, Clock, Info, Shield } from "lucide-react";
import { format } from "date-fns";
import { es } from "date-fns/locale";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { SEVERITY_CONFIG } from "@/lib/constants";
import type { AlertEvent } from "@/types/events";
import { AlertDetailMap } from "@/components/map/AlertDetailMap";

export const revalidate = 60;

/** Obtiene un evento individual desde el backend (SSR). */
async function getEvent(id: string): Promise<AlertEvent | null> {
  try {
    const host = process.env.API_URL || "http://127.0.0.1:8000";
    const apiBase = process.env.NEXT_PUBLIC_API_URL || `${host}/api/v1`;
    const res = await fetch(`${apiBase}/events/${id}`, {
      next: { revalidate: 60 },
    });

    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

/** Formatea una fecha ISO a formato legible. */
function formatDate(iso: string | null | undefined): string {
  if (!iso) return "—";
  try {
    return format(new Date(iso), "d MMM yyyy, HH:mm", { locale: es });
  } catch {
    return iso;
  }
}

/** Mapeo de event_type a etiqueta legible. */
const EVENT_TYPE_LABELS: Record<string, string> = {
  wind: "Viento",
  rain: "Lluvia",
  storm: "Tormenta",
  snow: "Nieve",
  ice: "Hielo",
  fog: "Niebla",
  heat: "Altas temperaturas",
  cold: "Bajas temperaturas",
  fire_risk: "Riesgo de incendio",
  coastal: "Costero",
  wave: "Oleaje",
  tide: "Mareas",
  earthquake: "Terremoto",
  tsunami: "Tsunami",
  traffic_accident: "Accidente de tráfico",
  traffic_closure: "Corte de tráfico",
  traffic_works: "Obras en vía",
  traffic_jam: "Retenciones",
  civil_protection: "Protección civil",
  uv: "Radiación UV",
  other: "Otro",
};

/** Mapeo de source a nombre legible. */
const SOURCE_LABELS: Record<string, string> = {
  aemet: "AEMET",
  ign: "IGN",
  dgt: "DGT",
  meteoalarm: "MeteoAlarm",
  esalert: "ESPAlert",
};

export default async function AlertDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const event = await getEvent(id);

  if (!event) {
    notFound();
  }

  const config = SEVERITY_CONFIG[event.severity] ?? SEVERITY_CONFIG.green;

  return (
    <main className="min-h-dvh bg-background">
      {/* Cabecera con barra de navegación */}
      <header className="sticky top-0 z-30 border-b bg-background/90 backdrop-blur-sm">
        <div className="mx-auto max-w-4xl flex items-center gap-3 px-4 py-3">
          <Link href="/">
            <Button variant="ghost" size="icon" className="shrink-0">
              <ArrowLeft size={20} />
              <span className="sr-only">Volver al mapa</span>
            </Button>
          </Link>
          <div className="flex-1 min-w-0">
            <h1 className="text-lg font-bold leading-tight truncate">
              {event.title}
            </h1>
            <p className="text-xs text-muted-foreground">
              {SOURCE_LABELS[event.source] ?? event.source} · {EVENT_TYPE_LABELS[event.event_type] ?? event.event_type}
            </p>
          </div>
          <Badge
            variant="outline"
            className={`font-semibold text-xs border uppercase tracking-wider shrink-0 ${config.color}`}
          >
            {config.label}
          </Badge>
        </div>
      </header>

      <div className="mx-auto max-w-4xl px-4 py-6 space-y-6">
        {/* Mini mapa con la geometría del evento */}
        {(event.area_geojson || event.area_name) && (
          <Card>
            <CardContent className="p-0 overflow-hidden rounded-xl">
              <div className="h-64 md:h-80">
                <AlertDetailMap event={event} />
              </div>
            </CardContent>
          </Card>
        )}

        {/* Información principal */}
        <div className="grid gap-4 md:grid-cols-2">
          {/* Línea temporal */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-sm">
                <Clock size={16} className="text-muted-foreground" />
                Línea temporal
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Inicio</span>
                <span className="font-medium">{formatDate(event.effective)}</span>
              </div>
              <Separator />
              <div className="flex justify-between">
                <span className="text-muted-foreground">Expiración</span>
                <span className="font-medium">{formatDate(event.expires)}</span>
              </div>
              <Separator />
              <div className="flex justify-between">
                <span className="text-muted-foreground">Registrado</span>
                <span className="font-medium">{formatDate(event.created_at)}</span>
              </div>
            </CardContent>
          </Card>

          {/* Ubicación y datos */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-sm">
                <MapPin size={16} className="text-muted-foreground" />
                Ubicación
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm">
              {event.area_name && (
                <>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Zona</span>
                    <span className="font-medium text-right max-w-[60%]">{event.area_name}</span>
                  </div>
                  <Separator />
                </>
              )}
              {event.magnitude && (
                <>
                  <div className="flex justify-between items-center">
                    <span className="text-muted-foreground">Magnitud</span>
                    <span className="font-semibold text-purple-500 flex items-center gap-1">
                      <Activity size={14} />
                      {event.magnitude}
                    </span>
                  </div>
                  <Separator />
                </>
              )}
              {event.depth_km && (
                <>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Profundidad</span>
                    <span className="font-medium">{event.depth_km} km</span>
                  </div>
                  <Separator />
                </>
              )}
              <div className="flex justify-between">
                <span className="text-muted-foreground">Fuente</span>
                <span className="font-medium">{SOURCE_LABELS[event.source] ?? event.source}</span>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Descripción */}
        {event.description && (
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-sm">
                <Info size={16} className="text-muted-foreground" />
                Descripción
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground leading-relaxed whitespace-pre-line">
                {event.description}
              </p>
            </CardContent>
          </Card>
        )}

        {/* Instrucciones de seguridad */}
        {event.instructions && (
          <Card className="border-yellow-500/30">
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-sm text-yellow-600 dark:text-yellow-400">
                <Shield size={16} />
                Instrucciones de seguridad
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm leading-relaxed whitespace-pre-line">
                {event.instructions}
              </p>
            </CardContent>
          </Card>
        )}

        {/* Enlace a fuente oficial */}
        {event.source_url && (
          <div className="flex justify-center">
            <a href={event.source_url} target="_blank" rel="noopener noreferrer">
              <Button variant="outline" className="gap-2">
                <ExternalLink size={16} />
                Ver en fuente oficial
              </Button>
            </a>
          </div>
        )}
      </div>
    </main>
  );
}
