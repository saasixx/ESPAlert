"use client";

import { useMemo, useRef, useState, useEffect } from "react";
import Map, { NavigationControl, Source, Layer } from "react-map-gl/maplibre";
import type { MapRef, LayerProps } from "react-map-gl/maplibre";
import { useTheme } from "next-themes";
import { Skeleton } from "@/components/ui/skeleton";
import type { AlertEvent } from "@/types/events";
import { useMapFilters } from "@/hooks/useMapFilters";
import { MapSidebar } from "@/components/sidebar/MapSidebar";
import "maplibre-gl/dist/maplibre-gl.css";

/** Colores según nivel de severidad. */
const SEVERITY_COLORS: Record<string, string> = {
  red: "#F44336",
  orange: "#FF9800",
  yellow: "#FFC107",
  green: "#4CAF50",
};

/** Estilos de mapa base (CARTO, gratuito). */
const CARTO_DARK = "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json";
const CARTO_LIGHT = "https://basemaps.cartocdn.com/gl/voyager-gl-style/style.json";

/** Vista inicial centrada en España. */
const INITIAL_VIEW = { longitude: -3.7, latitude: 40.0, zoom: 5.5 } as const;

export default function ESPAlertMap({
  events = [],
  isConnected = false,
}: {
  events: AlertEvent[];
  isConnected?: boolean;
}) {
  const mapRef = useRef<MapRef>(null);
  const { theme, systemTheme } = useTheme();
  const [mounted, setMounted] = useState(false);
  const { activeCategories, toggleCategory, getCategoryFromType } = useMapFilters();

  useEffect(() => {
    setMounted(true);
  }, []);

  const currentTheme = theme === "system" ? systemTheme : theme;
  const mapStyle = currentTheme === "light" ? CARTO_LIGHT : CARTO_DARK;

  // Filtrar eventos según los toggles activos de la barra lateral
  const visibleEvents = useMemo(
    () => events.filter((e) => activeCategories.has(getCategoryFromType(e.event_type))),
    [events, activeCategories, getCategoryFromType],
  );

  const polygonsGeoJSON = useMemo(
    () => ({
      type: "FeatureCollection" as const,
      features: visibleEvents
        .filter((e) => e.area_geojson?.type?.includes("Polygon"))
        .map((e) => ({
          type: "Feature" as const,
          geometry: e.area_geojson!,
          properties: {
            id: e.id,
            severity: e.severity,
            color: SEVERITY_COLORS[e.severity] ?? SEVERITY_COLORS.green,
            title: e.title,
          },
        })),
    }),
    [visibleEvents],
  );

  const pointsGeoJSON = useMemo(
    () => ({
      type: "FeatureCollection" as const,
      features: visibleEvents
        .filter((e) => e.area_geojson?.type === "Point")
        .map((e) => ({
          type: "Feature" as const,
          geometry: e.area_geojson!,
          properties: {
            id: e.id,
            severity: e.severity,
            type: e.event_type,
            color: SEVERITY_COLORS[e.severity] ?? SEVERITY_COLORS.green,
          },
        })),
    }),
    [visibleEvents],
  );

  if (!mounted) {
    return <Skeleton className="w-full h-full min-h-[500px]" />;
  }

  const fillLayerStyle: LayerProps = {
    id: "warning-areas-fill",
    type: "fill",
    paint: {
      "fill-color": ["get", "color"],
      "fill-opacity": 0.2,
    }
  };

  const lineLayerStyle: LayerProps = {
    id: "warning-areas-line",
    type: "line",
    paint: {
      "line-color": ["get", "color"],
      "line-width": 2,
      "line-opacity": 0.8,
    }
  };

  const circleLayerStyle: LayerProps = {
    id: "alert-points-circle",
    type: "circle",
    paint: {
      "circle-radius": [
        "match",
        ["get", "type"],
        "earthquake", 8,
        "tsunami", 8,
        6,
      ],
      "circle-color": ["get", "color"],
      "circle-opacity": 0.7,
      "circle-stroke-width": 2,
      "circle-stroke-color": ["get", "color"],
    }
  };

  return (
    <div className="w-full h-full flex absolute inset-0">
      <MapSidebar
        events={visibleEvents}
        activeCategories={activeCategories}
        toggleCategory={toggleCategory}
        isConnected={isConnected}
      />

      <div className="flex-1 relative">
        <Map
          ref={mapRef}
          initialViewState={INITIAL_VIEW}
          mapStyle={mapStyle}
          style={{ width: "100%", height: "100%" }}
          interactive
          maxZoom={18}
          minZoom={4}
        >
          <NavigationControl position="bottom-right" />

          <Source id="warning-areas" type="geojson" data={polygonsGeoJSON as any}>
            <Layer {...fillLayerStyle} />
            <Layer {...lineLayerStyle} />
          </Source>

          <Source id="alert-points" type="geojson" data={pointsGeoJSON as any}>
            <Layer {...circleLayerStyle} />
          </Source>
        </Map>
      </div>
    </div>
  );
}
