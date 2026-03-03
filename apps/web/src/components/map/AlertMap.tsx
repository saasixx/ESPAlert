"use client";

/**
 * AlertMap — Componente de mapa principal basado en mapcn.
 *
 * Reemplaza la implementación anterior con react-map-gl.
 * Usa MapLibre GL directamente a través de los componentes copypaste de mapcn,
 * que se integran nativamente con shadcn/ui y Tailwind CSS.
 */

import { useCallback, useMemo, useState } from "react";
import {
  Map,
  MapControls,
  MapPopup,
  MapClusterLayer,
  useMap,
} from "@/components/ui/map";
import type { AlertEvent, EventCategory } from "@/types/events";
import { useMapFilters } from "@/hooks/useMapFilters";
import { MapSidebar } from "@/components/sidebar/MapSidebar";
import { AlertPopup } from "@/components/map/AlertPopup";
import { AlertPolygonLayer } from "@/components/map/AlertPolygonLayer";
import { ConnectionIndicator } from "@/components/map/ConnectionIndicator";
import {
  SEVERITY_COLORS,
  SPAIN_CENTER,
  SPAIN_ZOOM,
  SPAIN_MIN_ZOOM,
} from "@/lib/constants";

interface AlertMapProps {
  events: AlertEvent[];
  isConnected?: boolean;
  connectionState?: string;
}

export default function AlertMap({
  events = [],
  isConnected = false,
  connectionState = "disconnected",
}: AlertMapProps) {
  const { activeCategories, toggleCategory, getCategoryFromType } =
    useMapFilters();
  const [selectedEvent, setSelectedEvent] = useState<AlertEvent | null>(null);

  // Filtrar eventos según las categorías activas
  const visibleEvents = useMemo(
    () =>
      events.filter((e) =>
        activeCategories.has(getCategoryFromType(e.event_type)),
      ),
    [events, activeCategories, getCategoryFromType],
  );

  // GeoJSON para eventos tipo punto (sismos, tráfico, etc.)
  const pointsGeoJSON = useMemo(
    (): GeoJSON.FeatureCollection<GeoJSON.Point> => ({
      type: "FeatureCollection",
      features: visibleEvents
        .filter((e) => e.area_geojson?.type === "Point")
        .map((e) => ({
          type: "Feature" as const,
          geometry: e.area_geojson as GeoJSON.Point,
          properties: {
            id: e.id,
            severity: e.severity,
            event_type: e.event_type,
            title: e.title,
            area_name: e.area_name ?? "",
            magnitude: e.magnitude ?? "",
            depth_km: e.depth_km ?? "",
            created_at: e.created_at,
            color: SEVERITY_COLORS[e.severity] ?? SEVERITY_COLORS.green,
          },
        })),
    }),
    [visibleEvents],
  );

  // Eventos con geometría de polígono (AEMET, MeteoAlarm)
  const polygonEvents = useMemo(
    () =>
      visibleEvents.filter(
        (e) =>
          e.area_geojson?.type === "Polygon" ||
          e.area_geojson?.type === "MultiPolygon",
      ),
    [visibleEvents],
  );

  // Callback cuando se hace clic en un punto del cluster layer
  const handlePointClick = useCallback(
    (feature: GeoJSON.Feature<GeoJSON.Point>) => {
      const props = feature.properties;
      if (!props?.id) return;
      const event = events.find((e) => e.id === props.id);
      if (event) setSelectedEvent(event);
    },
    [events],
  );

  // Callback cuando se hace clic en un polígono
  const handlePolygonClick = useCallback(
    (eventId: string) => {
      const event = events.find((e) => e.id === eventId);
      if (event) setSelectedEvent(event);
    },
    [events],
  );

  return (
    <div className="w-full h-full flex absolute inset-0">
      <MapSidebar
        events={visibleEvents}
        activeCategories={activeCategories}
        toggleCategory={toggleCategory}
        isConnected={isConnected}
        onEventClick={setSelectedEvent}
      />

      <div className="flex-1 relative">
        <Map
          center={SPAIN_CENTER}
          zoom={SPAIN_ZOOM}
          minZoom={SPAIN_MIN_ZOOM}
          maxZoom={18}
          renderWorldCopies={false}
          attributionControl={{ compact: true }}
        >
          <MapControls
            position="bottom-right"
            showZoom
            showCompass
            showLocate
            showFullscreen
          />

          {/* Capa de polígonos (avisos meteo, áreas de alerta) */}
          <AlertPolygonLayer
            events={polygonEvents}
            onEventClick={handlePolygonClick}
          />

          {/* Capa de puntos con clustering (sismos, tráfico) */}
          {pointsGeoJSON.features.length > 0 && (
            <MapClusterLayer
              data={pointsGeoJSON}
              clusterRadius={60}
              clusterMaxZoom={12}
              clusterColors={["#22c55e", "#eab308", "#ef4444"]}
              clusterThresholds={[10, 50]}
              pointColor="#3b82f6"
              onPointClick={handlePointClick}
            />
          )}

          {/* Popup de alerta seleccionada */}
          {selectedEvent && selectedEvent.area_geojson && (
            <SelectedEventPopup
              event={selectedEvent}
              onClose={() => setSelectedEvent(null)}
            />
          )}

          {/* Indicador de conexión */}
          <ConnectionIndicator
            isConnected={isConnected}
            connectionState={connectionState}
          />
        </Map>
      </div>
    </div>
  );
}

/** Popup para el evento seleccionado — necesita useMap() por lo que debe estar dentro de <Map>. */
function SelectedEventPopup({
  event,
  onClose,
}: {
  event: AlertEvent;
  onClose: () => void;
}) {
  const coords = getEventCoords(event);
  if (!coords) return null;

  return (
    <MapPopup
      longitude={coords[0]}
      latitude={coords[1]}
      onClose={onClose}
      closeButton
      offset={20}
    >
      <AlertPopup event={event} onClose={onClose} />
    </MapPopup>
  );
}

/** Extrae coordenadas [lon, lat] de un evento para posicionar el popup. */
function getEventCoords(event: AlertEvent): [number, number] | null {
  const geojson = event.area_geojson;
  if (!geojson) return null;

  if (geojson.type === "Point") {
    return geojson.coordinates as [number, number];
  }

  // Para polígonos, calcular centroide aproximado
  if (geojson.type === "Polygon") {
    const coords = geojson.coordinates[0];
    if (!coords?.length) return null;
    const lon = coords.reduce((s, c) => s + c[0], 0) / coords.length;
    const lat = coords.reduce((s, c) => s + c[1], 0) / coords.length;
    return [lon, lat];
  }

  if (geojson.type === "MultiPolygon") {
    const first = geojson.coordinates[0]?.[0];
    if (!first?.length) return null;
    const lon = first.reduce((s, c) => s + c[0], 0) / first.length;
    const lat = first.reduce((s, c) => s + c[1], 0) / first.length;
    return [lon, lat];
  }

  return null;
}
