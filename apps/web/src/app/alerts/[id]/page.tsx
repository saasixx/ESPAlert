import { notFound } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, ExternalLink, MapPin, Activity, Clock, Info, Shield } from "lucide-react";
import { format } from "date-fns";
import { es } from "date-fns/locale";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { SEVERITY_CONFIG, UI_STRINGS } from "@/lib/constants";
import type { AlertEvent } from "@/types/events";
import { AlertDetailMap } from "@/components/map/AlertDetailMap";

export const revalidate = 60;

/** Fetches a single event from the backend (SSR). */
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

/** Formats an ISO date to a readable format. */
function formatDate(iso: string | null | undefined): string {
  if (!iso) return "—";
  try {
    return format(new Date(iso), "d MMM yyyy, HH:mm", { locale: es });
  } catch {
    return iso;
  }
}

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
      {/* Header with navigation bar */}
      <header className="sticky top-0 z-30 border-b bg-background/90 backdrop-blur-sm">
        <div className="mx-auto max-w-4xl flex items-center gap-3 px-4 py-3">
          <Link href="/">
            <Button variant="ghost" size="icon" className="shrink-0">
              <ArrowLeft size={20} />
              <span className="sr-only">{UI_STRINGS.alertDetail.backToMap}</span>
            </Button>
          </Link>
          <div className="flex-1 min-w-0">
            <h1 className="text-lg font-bold leading-tight truncate">
              {event.title}
            </h1>
            <p className="text-xs text-muted-foreground">
              {UI_STRINGS.sourceLabels[event.source as keyof typeof UI_STRINGS.sourceLabels] ?? event.source} · {UI_STRINGS.eventTypeLabels[event.event_type as keyof typeof UI_STRINGS.eventTypeLabels] ?? event.event_type}
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
        {/* Mini map with event geometry */}
        {(event.area_geojson || event.area_name) && (
          <Card>
            <CardContent className="p-0 overflow-hidden rounded-xl">
              <div className="h-64 md:h-80">
                <AlertDetailMap event={event} />
              </div>
            </CardContent>
          </Card>
        )}

        {/* Main information */}
        <div className="grid gap-4 md:grid-cols-2">
          {/* Timeline */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-sm">
                <Clock size={16} className="text-muted-foreground" />
                {UI_STRINGS.alertDetail.timeline}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">{UI_STRINGS.alertDetail.start}</span>
                <span className="font-medium">{formatDate(event.effective)}</span>
              </div>
              <Separator />
              <div className="flex justify-between">
                <span className="text-muted-foreground">{UI_STRINGS.alertDetail.expiration}</span>
                <span className="font-medium">{formatDate(event.expires)}</span>
              </div>
              <Separator />
              <div className="flex justify-between">
                <span className="text-muted-foreground">{UI_STRINGS.alertDetail.recorded}</span>
                <span className="font-medium">{formatDate(event.created_at)}</span>
              </div>
            </CardContent>
          </Card>

          {/* Location and data */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-sm">
                <MapPin size={16} className="text-muted-foreground" />
                {UI_STRINGS.alertDetail.location}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm">
              {event.area_name && (
                <>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">{UI_STRINGS.alertDetail.area}</span>
                    <span className="font-medium text-right max-w-[60%]">{event.area_name}</span>
                  </div>
                  <Separator />
                </>
              )}
              {event.magnitude && (
                <>
                  <div className="flex justify-between items-center">
                    <span className="text-muted-foreground">{UI_STRINGS.alertDetail.magnitude}</span>
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
                    <span className="text-muted-foreground">{UI_STRINGS.alertDetail.depth}</span>
                    <span className="font-medium">{event.depth_km} km</span>
                  </div>
                  <Separator />
                </>
              )}
              <div className="flex justify-between">
                <span className="text-muted-foreground">{UI_STRINGS.alertDetail.source}</span>
                <span className="font-medium">{UI_STRINGS.sourceLabels[event.source as keyof typeof UI_STRINGS.sourceLabels] ?? event.source}</span>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Description */}
        {event.description && (
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-sm">
                <Info size={16} className="text-muted-foreground" />
                {UI_STRINGS.alertDetail.description}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground leading-relaxed whitespace-pre-line">
                {event.description}
              </p>
            </CardContent>
          </Card>
        )}

        {/* Safety instructions */}
        {event.instructions && (
          <Card className="border-yellow-500/30">
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-sm text-yellow-600 dark:text-yellow-400">
                <Shield size={16} />
                {UI_STRINGS.alertDetail.safetyInstructions}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm leading-relaxed whitespace-pre-line">
                {event.instructions}
              </p>
            </CardContent>
          </Card>
        )}

        {/* Link to official source */}
        {event.source_url && (
          <div className="flex justify-center">
            <a href={event.source_url} target="_blank" rel="noopener noreferrer">
              <Button variant="outline" className="gap-2">
                <ExternalLink size={16} />
                {UI_STRINGS.alertDetail.officialSource}
              </Button>
            </a>
          </div>
        )}
      </div>
    </main>
  );
}
