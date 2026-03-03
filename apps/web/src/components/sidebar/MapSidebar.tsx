"use client";

import { clsx } from "clsx";
import { formatDistanceToNow } from "date-fns";
import { es } from "date-fns/locale";
import { Activity, Car, CloudRain, MapPin, Waves } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import type { AlertEvent, EventCategory } from "@/types/events";
import { SEVERITY_CONFIG } from "@/lib/constants";

interface MapSidebarProps {
  events: AlertEvent[];
  activeCategories: Set<EventCategory>;
  toggleCategory: (category: EventCategory) => void;
  isConnected: boolean;
  onEventClick?: (event: AlertEvent) => void;
}

export function MapSidebar({ events, activeCategories, toggleCategory, isConnected, onEventClick }: MapSidebarProps) {
  const summary = events.reduce(
    (acc, event) => {
      acc.total += 1;
      acc[event.severity] += 1;
      return acc;
    },
    { total: 0, red: 0, orange: 0, yellow: 0, green: 0 }
  );

  const recommendedActions = Array.from(
    new Set(
      events
        .filter((event) => event.severity === "red" || event.severity === "orange")
        .map((event) => event.instructions?.trim())
        .filter((instruction): instruction is string => Boolean(instruction))
    )
  ).slice(0, 3);

  return (
    <div className="w-96 flex flex-col bg-background/90 backdrop-blur-xl border-r h-full shadow-2xl relative z-10 transition-all">
      {/* Encabezado */}
      <div className="p-6 border-b bg-background/50">
        <h1 className="text-2xl font-bold flex items-center gap-2">
          🛡️ ESPAlert
        </h1>
        <p className="text-sm text-muted-foreground mt-1">Alertas en tiempo real para España</p>
        <div className="mt-3 flex items-center gap-2 text-xs">
          <span className={clsx("h-2.5 w-2.5 rounded-full", isConnected ? "bg-green-500" : "bg-yellow-500")} />
          <span className="text-muted-foreground">
            {isConnected ? "Conectado a eventos en vivo" : "Modo respaldo (sin conexión en vivo)"}
          </span>
        </div>
      </div>

      <div className="p-4 border-b grid grid-cols-2 gap-2 text-xs">
        <SummaryPill label="Alertas activas" value={summary.total} tone="default" />
        <SummaryPill label="Extremas" value={summary.red} tone="red" />
        <SummaryPill label="Importantes" value={summary.orange} tone="orange" />
        <SummaryPill label="Riesgo moderado" value={summary.yellow} tone="yellow" />
      </div>

      {/* Filtros por categoría */}
      <div className="p-4 border-b grid grid-cols-2 gap-2">
        <FilterButton 
          active={activeCategories.has('meteo')} 
          onClick={() => toggleCategory('meteo')}
          icon={<CloudRain size={16} />}
          label="Meteo"
        />
        <FilterButton 
          active={activeCategories.has('seismic')} 
          onClick={() => toggleCategory('seismic')}
          icon={<Activity size={16} />}
          label="Sismos"
        />
        <FilterButton 
          active={activeCategories.has('traffic')} 
          onClick={() => toggleCategory('traffic')}
          icon={<Car size={16} />}
          label="Tráfico"
        />
        <FilterButton 
          active={activeCategories.has('maritime')} 
          onClick={() => toggleCategory('maritime')}
          icon={<Waves size={16} />}
          label="Costero"
        />
      </div>

      {/* Lista de eventos */}
      <ScrollArea className="flex-1 p-4">
        <div className="flex flex-col gap-3 pb-8">
          {recommendedActions.length > 0 && (
            <section className="rounded-xl border bg-card p-4">
              <h2 className="text-sm font-semibold mb-2">Acciones recomendadas</h2>
              <ul className="space-y-2 text-xs text-muted-foreground">
                {recommendedActions.map((action) => (
                  <li key={action} className="leading-relaxed">
                    • {action}
                  </li>
                ))}
              </ul>
            </section>
          )}

          {events.length === 0 ? (
            <div className="text-center p-8 text-muted-foreground">
              <MapPin className="mx-auto mb-2 opacity-50" size={32} />
              <p>No hay alertas activas para los filtros seleccionados.</p>
            </div>
          ) : (
            events.slice(0, 100).map(event => (
              <EventCard key={event.id} event={event} onClick={() => onEventClick?.(event)} />
            ))
          )}
        </div>
      </ScrollArea>
    </div>
  );
}

function SummaryPill({
  label,
  value,
  tone,
}: {
  label: string;
  value: number;
  tone: "default" | "red" | "orange" | "yellow";
}) {
  const toneClass = {
    default: "bg-muted text-foreground border-border",
    red: "bg-red-500/15 text-red-500 border-red-500/40",
    orange: "bg-orange-500/15 text-orange-500 border-orange-500/40",
    yellow: "bg-yellow-500/15 text-yellow-500 border-yellow-500/40",
  }[tone];

  return (
    <div className={clsx("rounded-lg border px-3 py-2", toneClass)}>
      <p className="text-[11px] opacity-90">{label}</p>
      <p className="text-lg font-semibold leading-tight">{value}</p>
    </div>
  );
}

function FilterButton({ active, onClick, icon, label }: { active: boolean, onClick: () => void, icon: React.ReactNode, label: string }) {
  return (
    <Button
      variant={active ? "default" : "outline"}
      className={clsx(
        "justify-start gap-2 h-10 w-full transition-all",
        active ? "bg-primary text-primary-foreground shadow-md" : "opacity-70 hover:opacity-100"
      )}
      onClick={onClick}
    >
      {icon}
      {label}
    </Button>
  );
}

function EventCard({ event, onClick }: { event: AlertEvent; onClick?: () => void }) {
  const config = SEVERITY_CONFIG[event.severity] ?? SEVERITY_CONFIG.green;
  
  return (
    <div
      className="rounded-xl border bg-card text-card-foreground shadow-sm hover:shadow-md hover:border-primary/50 transition-all cursor-pointer overflow-hidden"
      onClick={onClick}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') onClick?.(); }}
    >
      <div className="p-4 flex flex-col gap-2">
        <div className="flex justify-between items-start gap-2">
          <Badge variant="outline" className={clsx("font-semibold text-xs border uppercase tracking-wider", config.color)}>
            {config.label}
          </Badge>
          <span className="text-xs text-muted-foreground whitespace-nowrap">
            {formatDistanceToNow(new Date(event.created_at), { addSuffix: true, locale: es })}
          </span>
        </div>
        
        <h3 className="font-semibold text-sm leading-tight line-clamp-2">
          {event.title}
        </h3>
        
        {event.area_name && (
          <div className="flex items-center gap-1.5 text-xs text-muted-foreground mt-1">
            <MapPin size={12} className="shrink-0" />
            <span className="truncate">{event.area_name}</span>
          </div>
        )}

        {event.magnitude && (
          <div className="flex items-center gap-1.5 text-xs font-medium text-purple-400 mt-1">
            <Activity size={12} />
            Magnitud: {event.magnitude} {event.depth_km && `• Profundidad: ${event.depth_km} km`}
          </div>
        )}
      </div>
    </div>
  );
}