"use client"

import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { EventCategory, AlertEvent } from "@/types/events";
import { formatDistanceToNow } from "date-fns";
import { es } from "date-fns/locale";
import { CloudRain, Activity, Car, Waves, MapPin, AlertTriangle } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { clsx } from "clsx";

interface MapSidebarProps {
  events: AlertEvent[];
  activeCategories: Set<EventCategory>;
  toggleCategory: (category: EventCategory) => void;
}

const severityConfig = {
  red: { color: "bg-red-500/20 text-red-500 border-red-500/50", label: "RIESGO EXTREMO" },
  orange: { color: "bg-orange-500/20 text-orange-500 border-orange-500/50", label: "IMPORTANTE" },
  yellow: { color: "bg-yellow-500/20 text-yellow-500 border-yellow-500/50", label: "RIESGO" },
  green: { color: "bg-green-500/20 text-green-500 border-green-500/50", label: "SIN RIESGO" },
};

export function MapSidebar({ events, activeCategories, toggleCategory }: MapSidebarProps) {
  return (
    <div className="w-96 flex flex-col bg-background/90 backdrop-blur-xl border-r h-full shadow-2xl relative z-10 transition-all">
      {/* Header */}
      <div className="p-6 border-b bg-background/50">
        <h1 className="text-2xl font-bold flex items-center gap-2">
          🛡️ ESPAlert 
        </h1>
        <p className="text-sm text-muted-foreground mt-1">Alertas en tiempo real</p>
      </div>

      {/* Filters */}
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

      {/* Event List */}
      <ScrollArea className="flex-1 p-4">
        <div className="flex flex-col gap-3 pb-8">
          {events.length === 0 ? (
            <div className="text-center p-8 text-muted-foreground">
              <MapPin className="mx-auto mb-2 opacity-50" size={32} />
              No hay alertas activas para los filtros seleccionados.
            </div>
          ) : (
            events.slice(0, 100).map(event => (
              <EventCard key={event.id} event={event} />
            ))
          )}
        </div>
      </ScrollArea>
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

function EventCard({ event }: { event: AlertEvent }) {
  const config = severityConfig[event.severity as keyof typeof severityConfig] || severityConfig.green;
  
  return (
    <div className="rounded-xl border bg-card text-card-foreground shadow-sm hover:shadow-md hover:border-primary/50 transition-all cursor-pointer overflow-hidden">
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
            Mag: {event.magnitude} {event.depth_km && `• Prof: ${event.depth_km}km`}
          </div>
        )}
      </div>
    </div>
  );
}