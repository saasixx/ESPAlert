"use client";

/**
 * AlertPolygonLayer — Renderiza polígonos de avisos meteorológicos y áreas de alerta.
 *
 * Usa useMap() de mapcn para acceder al MapLibre map instance directamente
 * y añade sources/layers de GeoJSON de polígonos con colores por severidad.
 */

import { useEffect, useMemo, useRef } from "react";
import { useMap } from "@/components/ui/map";
import type { AlertEvent } from "@/types/events";
import { SEVERITY_COLORS, SEVERITY_FILL_OPACITY } from "@/lib/constants";

interface AlertPolygonLayerProps {
  events: AlertEvent[];
  onEventClick?: (eventId: string) => void;
}

const SOURCE_ID = "espalert-polygons";
const FILL_LAYER_ID = "espalert-polygons-fill";
const LINE_LAYER_ID = "espalert-polygons-line";

export function AlertPolygonLayer({
  events,
  onEventClick,
}: AlertPolygonLayerProps) {
  const { map, isLoaded } = useMap();
  const onClickRef = useRef(onEventClick);
  onClickRef.current = onEventClick;

  // Construir GeoJSON FeatureCollection
  const geojson = useMemo(
    (): GeoJSON.FeatureCollection => ({
      type: "FeatureCollection",
      features: events
        .filter(
          (e) =>
            e.area_geojson?.type === "Polygon" ||
            e.area_geojson?.type === "MultiPolygon",
        )
        .map((e) => ({
          type: "Feature" as const,
          geometry: e.area_geojson!,
          properties: {
            id: e.id,
            severity: e.severity,
            color: SEVERITY_COLORS[e.severity] ?? SEVERITY_COLORS.green,
            opacity:
              SEVERITY_FILL_OPACITY[e.severity] ?? SEVERITY_FILL_OPACITY.green,
            title: e.title,
          },
        })),
    }),
    [events],
  );

  // Inicializar source y layers
  useEffect(() => {
    if (!isLoaded || !map) return;

    // Añadir source
    map.addSource(SOURCE_ID, {
      type: "geojson",
      data: geojson,
    });

    // Capa de relleno
    map.addLayer({
      id: FILL_LAYER_ID,
      type: "fill",
      source: SOURCE_ID,
      paint: {
        "fill-color": ["get", "color"],
        "fill-opacity": ["get", "opacity"],
      },
    });

    // Capa de borde
    map.addLayer({
      id: LINE_LAYER_ID,
      type: "line",
      source: SOURCE_ID,
      paint: {
        "line-color": ["get", "color"],
        "line-width": 2,
        "line-opacity": 0.8,
      },
    });

    return () => {
      try {
        if (map.getLayer(LINE_LAYER_ID)) map.removeLayer(LINE_LAYER_ID);
        if (map.getLayer(FILL_LAYER_ID)) map.removeLayer(FILL_LAYER_ID);
        if (map.getSource(SOURCE_ID)) map.removeSource(SOURCE_ID);
      } catch {
        // El mapa puede haber sido destruido
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isLoaded, map]);

  // Actualizar datos cuando cambian los eventos
  useEffect(() => {
    if (!isLoaded || !map) return;
    const source = map.getSource(SOURCE_ID) as maplibregl.GeoJSONSource;
    if (source) {
      source.setData(geojson);
    }
  }, [isLoaded, map, geojson]);

  // Manejar clicks en polígonos
  useEffect(() => {
    if (!isLoaded || !map) return;

    const handleClick = (e: maplibregl.MapMouseEvent & { features?: maplibregl.MapGeoJSONFeature[] }) => {
      const features = map.queryRenderedFeatures(e.point, {
        layers: [FILL_LAYER_ID],
      });
      if (features.length > 0) {
        const eventId = features[0].properties?.id;
        if (eventId) onClickRef.current?.(eventId);
      }
    };

    const handleMouseEnter = () => {
      map.getCanvas().style.cursor = "pointer";
    };

    const handleMouseLeave = () => {
      map.getCanvas().style.cursor = "";
    };

    map.on("click", FILL_LAYER_ID, handleClick);
    map.on("mouseenter", FILL_LAYER_ID, handleMouseEnter);
    map.on("mouseleave", FILL_LAYER_ID, handleMouseLeave);

    return () => {
      map.off("click", FILL_LAYER_ID, handleClick);
      map.off("mouseenter", FILL_LAYER_ID, handleMouseEnter);
      map.off("mouseleave", FILL_LAYER_ID, handleMouseLeave);
    };
  }, [isLoaded, map]);

  return null;
}
