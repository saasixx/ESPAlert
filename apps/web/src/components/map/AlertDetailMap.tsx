"use client";

/**
 * AlertDetailMap — Mini mapa para la página de detalle de una alerta.
 * Muestra la geometría del evento o un marcador centroide si no tiene geometría.
 */

import { useMemo } from "react";
import { Map, MapMarker, MarkerContent } from "@/components/ui/map";
import { AlertPolygonLayer } from "@/components/map/AlertPolygonLayer";
import type { AlertEvent } from "@/types/events";
import { SEVERITY_COLORS } from "@/lib/constants";
import { resolveAreaCentroid } from "@/lib/area-centroids";

interface AlertDetailMapProps {
  event: AlertEvent;
}

export function AlertDetailMap({ event }: AlertDetailMapProps) {
  const coords = useMemo(() => getCoords(event), [event]);

  const polygonEvents = useMemo(
    () =>
      event.area_geojson?.type === "Polygon" ||
      event.area_geojson?.type === "MultiPolygon"
        ? [event]
        : [],
    [event],
  );

  if (!coords) return null;

  const color = SEVERITY_COLORS[event.severity] ?? SEVERITY_COLORS.green;

  return (
    <Map
      center={coords}
      zoom={event.area_geojson?.type === "Point" ? 10 : 7}
      attributionControl={{ compact: true }}
      interactive={true}
    >
      {/* Polígono si lo hay */}
      <AlertPolygonLayer events={polygonEvents} />

      {/* Marcador punto */}
      {(event.area_geojson?.type === "Point" || !event.area_geojson) && (
        <MapMarker longitude={coords[0]} latitude={coords[1]}>
          <MarkerContent>
            <div
              className="h-4 w-4 rounded-full border-2 border-white shadow-lg"
              style={{ backgroundColor: color }}
            />
          </MarkerContent>
        </MapMarker>
      )}
    </Map>
  );
}

/** Extrae coordenadas [lon, lat] del evento. */
function getCoords(event: AlertEvent): [number, number] | null {
  const geo = event.area_geojson;

  if (geo?.type === "Point") {
    return geo.coordinates as [number, number];
  }

  if (geo?.type === "Polygon") {
    const ring = geo.coordinates[0];
    if (!ring?.length) return null;
    const lon = ring.reduce((s, c) => s + c[0], 0) / ring.length;
    const lat = ring.reduce((s, c) => s + c[1], 0) / ring.length;
    return [lon, lat];
  }

  if (geo?.type === "MultiPolygon") {
    const first = geo.coordinates[0]?.[0];
    if (!first?.length) return null;
    const lon = first.reduce((s, c) => s + c[0], 0) / first.length;
    const lat = first.reduce((s, c) => s + c[1], 0) / first.length;
    return [lon, lat];
  }

  // Fallback: centroide por nombre de área
  return resolveAreaCentroid(event.area_name);
}
