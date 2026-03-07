"use client";

/**
 * AlertMap — Main map component based on mapcn.
 *
 * Uses mapcn components (https://github.com/AnmolSaini16/mapcn)
 * that integrate natively with shadcn/ui and Tailwind CSS.
 */

import { useCallback, useMemo, useState } from "react";
import {
  Map,
  MapControls,
  MapPopup,
} from "@/components/ui/map";
import type { AlertEvent } from "@/types/events";
import { useMapFilters } from "@/hooks/useMapFilters";
import { MapSidebar } from "@/components/sidebar/MapSidebar";
import { AlertPopup } from "@/components/map/AlertPopup";
import { AlertPolygonLayer } from "@/components/map/AlertPolygonLayer";
import { AlertIconLayer } from "@/components/map/AlertIconLayer";
import { ConnectionIndicator } from "@/components/map/ConnectionIndicator";
import {
  SPAIN_CENTER,
  SPAIN_ZOOM,
  SPAIN_MIN_ZOOM,
  getEventCategory,
} from "@/lib/constants";
import { resolveAreaCentroid } from "@/lib/area-centroids";

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

  // Filter events based on active categories
  const visibleEvents = useMemo(
    () =>
      events.filter((e) =>
        activeCategories.has(getCategoryFromType(e.event_type)),
      ),
    [events, activeCategories, getCategoryFromType],
  );

  // GeoJSON for point-type events (earthquakes, traffic, etc.) + centroid fallback
  const pointsGeoJSON = useMemo(
    (): GeoJSON.FeatureCollection<GeoJSON.Point> => ({
      type: "FeatureCollection",
      features: visibleEvents
        .map((e) => {
          const category = getEventCategory(e.event_type, e.icon_key);
          const baseProps = {
            id: e.id,
            severity: e.severity,
            category,
            event_type: e.event_type,
            title: e.title,
            area_name: e.area_name ?? "",
            magnitude: e.magnitude ?? "",
            depth_km: e.depth_km ?? "",
            created_at: e.created_at,
          };

          // Event with native Point geometry
          if (e.area_geojson?.type === "Point") {
            return {
              type: "Feature" as const,
              geometry: e.area_geojson as GeoJSON.Point,
              properties: baseProps,
            };
          }

          // Event without geometry → resolve centroid by area_name
          if (!e.area_geojson) {
            const centroid = resolveAreaCentroid(e.area_name);
            if (centroid) {
              return {
                type: "Feature" as const,
                geometry: {
                  type: "Point" as const,
                  coordinates: centroid,
                },
                properties: baseProps,
              };
            }
          }

          return null;
        })
        .filter((f): f is NonNullable<typeof f> => f !== null),
    }),
    [visibleEvents],
  );

  // Events with polygon geometry (AEMET, MeteoAlarm)
  const polygonEvents = useMemo(
    () =>
      visibleEvents.filter(
        (e) =>
          e.area_geojson?.type === "Polygon" ||
          e.area_geojson?.type === "MultiPolygon",
      ),
    [visibleEvents],
  );

  // Callback when a cluster layer point is clicked
  const handlePointClick = useCallback(
    (feature: GeoJSON.Feature<GeoJSON.Point>) => {
      const props = feature.properties;
      if (!props?.id) return;
      const event = events.find((e) => e.id === props.id);
      if (event) setSelectedEvent(event);
    },
    [events],
  );

  // Callback when a polygon is clicked
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

          {/* Polygon layer (meteo warnings, alert areas) */}
          <AlertPolygonLayer
            events={polygonEvents}
            onEventClick={handlePolygonClick}
          />

          {/* Point layer with clustering and category icons (earthquakes, traffic, meteo) */}
          {pointsGeoJSON.features.length > 0 && (
            <AlertIconLayer
              data={pointsGeoJSON}
              onPointClick={handlePointClick}
            />
          )}

          {/* Selected alert popup */}
          {selectedEvent && (
            <SelectedEventPopup
              event={selectedEvent}
              onClose={() => setSelectedEvent(null)}
            />
          )}

          {/* Connection indicator */}
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

  if (geojson) {
    if (geojson.type === "Point") {
      return geojson.coordinates as [number, number];
    }

    // For polygons, compute approximate centroid
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
  }

  // Fallback: resolver centroide por area_name
  return resolveAreaCentroid(event.area_name);
}
