"use client";

/**
 * AlertPopup — Contenido del popup que se muestra al seleccionar una alerta en el mapa.
 * Diseñado para usarse dentro de componentes popup de mapcn.
 */

import { formatDistanceToNow } from "date-fns";
import { es } from "date-fns/locale";
import { Activity, ExternalLink, MapPin } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import type { AlertEvent } from "@/types/events";
import { SEVERITY_CONFIG } from "@/lib/constants";

interface AlertPopupProps {
  event: AlertEvent;
  onClose?: () => void;
}

export function AlertPopup({ event }: AlertPopupProps) {
  const config = SEVERITY_CONFIG[event.severity] ?? SEVERITY_CONFIG.green;

  return (
    <div className="w-72 space-y-2">
      <div className="flex items-start justify-between gap-2">
        <Badge
          variant="outline"
          className={`font-semibold text-xs border uppercase tracking-wider ${config.color}`}
        >
          {config.label}
        </Badge>
        <span className="text-xs text-muted-foreground whitespace-nowrap">
          {formatDistanceToNow(new Date(event.created_at), {
            addSuffix: true,
            locale: es,
          })}
        </span>
      </div>

      <h3 className="font-semibold text-sm leading-tight">{event.title}</h3>

      {event.area_name && (
        <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
          <MapPin size={12} className="shrink-0" />
          <span className="truncate">{event.area_name}</span>
        </div>
      )}

      {event.magnitude && (
        <div className="flex items-center gap-1.5 text-xs font-medium text-purple-400">
          <Activity size={12} />
          Magnitud: {event.magnitude}
          {event.depth_km && ` • Prof: ${event.depth_km} km`}
        </div>
      )}

      {event.description && (
        <p className="text-xs text-muted-foreground line-clamp-3 leading-relaxed">
          {event.description}
        </p>
      )}

      {event.source_url && (
        <a
          href={event.source_url}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1 text-xs text-primary hover:underline"
        >
          <ExternalLink size={10} />
          Ver fuente oficial
        </a>
      )}
    </div>
  );
}
