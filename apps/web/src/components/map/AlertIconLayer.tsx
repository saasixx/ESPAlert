"use client";

/**
 * AlertIconLayer — Renders point events with differentiated icons by category and severity.
 *
 * Replaces the generic MapClusterLayer with category-aware icons:
 * - meteo: cloud/rain (AEMET, MeteoAlarm)
 * - seismic: wave/tremor (IGN)
 * - traffic: road warning (DGT)
 * - maritime: anchor/waves (coastal alerts)
 *
 * Each category has 4 severity variants (green/yellow/orange/red).
 * Clusters are shown as colored circles with a count label.
 */

import { useEffect, useRef } from "react";
import { useMap } from "@/components/ui/map";
import { SEVERITY_COLORS } from "@/lib/constants";

interface AlertIconLayerProps {
  data: GeoJSON.FeatureCollection<GeoJSON.Point>;
  onPointClick?: (feature: GeoJSON.Feature<GeoJSON.Point>) => void;
}

const SOURCE_ID = "espalert-points";
const CLUSTER_CIRCLE_ID = "espalert-clusters";
const CLUSTER_COUNT_ID = "espalert-cluster-count";
const UNCLUSTERED_ID = "espalert-unclustered";

// Lucide-style SVG icon paths (24×24 viewBox) for each category
const CATEGORY_ICON_PATHS: Record<string, string> = {
  // Cloud with rain drops — meteo/weather
  meteo: "M17 18a5 5 0 0 0-10 0 M12 9v2 M12 2v1 M4.2 4.2l.7.7 M19.8 4.2l-.7.7 M2 13h1 M21 13h-1 M6 13a6 6 0 0 1 12 0 M8 18l-.5 2 M12 18v2 M16 18l.5 2",
  // Seismic waveform — earthquakes
  seismic: "M2 12h3l2-6 3 12 2-9 2 6 2-3h4",
  // Triangle warning with exclamation — traffic incidents
  traffic: "M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z M12 9v4 M12 17h.01",
  // Anchor — maritime/coastal
  maritime: "M12 2a3 3 0 1 1 0 6 3 3 0 0 1 0-6z M12 8v14 M5 15h14 M5 15C5 19 8 22 12 22s7-3 7-7",
};

const SEVERITIES = ["green", "yellow", "orange", "red"] as const;
const CATEGORIES = ["meteo", "seismic", "traffic", "maritime"] as const;
const ICON_SIZE = 28;

/** Generates a colored SVG circle icon with a white stroked path inside. */
function createIconSVG(iconPath: string, color: string): string {
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${ICON_SIZE}" height="${ICON_SIZE}" viewBox="0 0 ${ICON_SIZE} ${ICON_SIZE}">
  <circle cx="${ICON_SIZE / 2}" cy="${ICON_SIZE / 2}" r="${ICON_SIZE / 2 - 1}" fill="${color}" fill-opacity="0.92"/>
  <circle cx="${ICON_SIZE / 2}" cy="${ICON_SIZE / 2}" r="${ICON_SIZE / 2 - 1}" fill="none" stroke="white" stroke-width="1.5"/>
  <g transform="translate(${(ICON_SIZE - 18) / 2}, ${(ICON_SIZE - 18) / 2}) scale(0.75)">
    <path d="${iconPath}" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
  </g>
</svg>`;
}

/** Returns the icon key string used as MapLibre image name. */
export function getIconKey(category: string, severity: string): string {
  return `espalert-icon-${category}-${severity}`;
}

/** Loads all 16 category×severity icon images and registers them in the map. */
async function registerIcons(
  map: maplibregl.Map,
): Promise<void> {
  const promises: Promise<void>[] = [];

  for (const category of CATEGORIES) {
    const path = CATEGORY_ICON_PATHS[category];
    for (const severity of SEVERITIES) {
      const key = getIconKey(category, severity);
      if (map.hasImage(key)) continue;

      const color = SEVERITY_COLORS[severity];
      const svg = createIconSVG(path, color);
      const dataURL = `data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg)}`;

      const p = new Promise<void>((resolve, reject) => {
        const img = new Image(ICON_SIZE, ICON_SIZE);
        img.onload = () => {
          if (!map.hasImage(key)) {
            map.addImage(key, img);
          }
          resolve();
        };
        img.onerror = reject;
        img.src = dataURL;
      });

      promises.push(p);
    }
  }

  await Promise.all(promises);
}

/** Cluster background color based on cluster point_count. */
const CLUSTER_COLOR_EXPR = [
  "step",
  ["get", "point_count"],
  "#64748b", // slate-500 for small clusters
  10,
  "#f97316", // orange for medium
  50,
  "#ef4444", // red for large
] as maplibregl.ExpressionSpecification;

export function AlertIconLayer({ data, onPointClick }: AlertIconLayerProps) {
  const { map, isLoaded } = useMap();
  const onClickRef = useRef(onPointClick);
  onClickRef.current = onPointClick;
  const iconsLoadedRef = useRef(false);

  // Initialize source and layers once
  useEffect(() => {
    if (!isLoaded || !map) return;

    let cancelled = false;

    async function setup() {
      if (!map) return;
      // Register icons first
      await registerIcons(map);
      if (cancelled || !map) return;

      iconsLoadedRef.current = true;

      // Source with clustering enabled
      if (!map.getSource(SOURCE_ID)) {
        map.addSource(SOURCE_ID, {
          type: "geojson",
          data,
          cluster: true,
          clusterRadius: 60,
          clusterMaxZoom: 12,
        });
      }

      // Cluster bubble
      if (!map.getLayer(CLUSTER_CIRCLE_ID)) {
        map.addLayer({
          id: CLUSTER_CIRCLE_ID,
          type: "circle",
          source: SOURCE_ID,
          filter: ["has", "point_count"],
          paint: {
            "circle-color": CLUSTER_COLOR_EXPR,
            "circle-radius": [
              "step",
              ["get", "point_count"],
              18,
              10,
              24,
              50,
              30,
            ],
            "circle-opacity": 0.88,
            "circle-stroke-width": 2,
            "circle-stroke-color": "rgba(255,255,255,0.6)",
          },
        });
      }

      // Cluster count label
      if (!map.getLayer(CLUSTER_COUNT_ID)) {
        map.addLayer({
          id: CLUSTER_COUNT_ID,
          type: "symbol",
          source: SOURCE_ID,
          filter: ["has", "point_count"],
          layout: {
            "text-field": ["get", "point_count_abbreviated"],
            "text-font": ["Noto Sans Bold", "Open Sans Bold"],
            "text-size": 13,
          },
          paint: {
            "text-color": "#ffffff",
          },
        });
      }

      // Individual point icons (icon-image = espalert-icon-{category}-{severity})
      if (!map.getLayer(UNCLUSTERED_ID)) {
        map.addLayer({
          id: UNCLUSTERED_ID,
          type: "symbol",
          source: SOURCE_ID,
          filter: ["!", ["has", "point_count"]],
          layout: {
            "icon-image": [
              "concat",
              "espalert-icon-",
              ["get", "category"],
              "-",
              ["get", "severity"],
            ],
            "icon-size": 1,
            "icon-allow-overlap": true,
            "icon-anchor": "center",
          },
        });
      }
    }

    setup();

    return () => {
      cancelled = true;
      try {
        if (map.getLayer(CLUSTER_COUNT_ID)) map.removeLayer(CLUSTER_COUNT_ID);
        if (map.getLayer(CLUSTER_CIRCLE_ID)) map.removeLayer(CLUSTER_CIRCLE_ID);
        if (map.getLayer(UNCLUSTERED_ID)) map.removeLayer(UNCLUSTERED_ID);
        if (map.getSource(SOURCE_ID)) map.removeSource(SOURCE_ID);
      } catch {
        // Map may have been destroyed
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isLoaded, map]);

  // Update data when events change
  useEffect(() => {
    if (!isLoaded || !map) return;
    const source = map.getSource(SOURCE_ID) as maplibregl.GeoJSONSource | undefined;
    if (source) {
      source.setData(data);
    }
  }, [isLoaded, map, data]);

  // Click handler for individual points
  useEffect(() => {
    if (!isLoaded || !map) return;

    const handlePointClick = (
      e: maplibregl.MapMouseEvent & {
        features?: maplibregl.MapGeoJSONFeature[];
      },
    ) => {
      const features = map.queryRenderedFeatures(e.point, {
        layers: [UNCLUSTERED_ID],
      });
      if (features.length > 0) {
        onClickRef.current?.(
          features[0] as unknown as GeoJSON.Feature<GeoJSON.Point>,
        );
      }
    };

    // Click on cluster → zoom in
    const handleClusterClick = (
      e: maplibregl.MapMouseEvent & {
        features?: maplibregl.MapGeoJSONFeature[];
      },
    ) => {
      const features = map.queryRenderedFeatures(e.point, {
        layers: [CLUSTER_CIRCLE_ID],
      });
      if (!features.length) return;
      const clusterId = features[0].properties?.cluster_id;
      const source = map.getSource(SOURCE_ID) as maplibregl.GeoJSONSource;
      source.getClusterExpansionZoom(clusterId).then((zoom) => {
        const coords = (features[0].geometry as GeoJSON.Point).coordinates;
        map.easeTo({ center: [coords[0], coords[1]], zoom });
      }).catch(() => {});
    };

    const setCursorPointer = () => {
      map.getCanvas().style.cursor = "pointer";
    };
    const resetCursor = () => {
      map.getCanvas().style.cursor = "";
    };

    map.on("click", UNCLUSTERED_ID, handlePointClick);
    map.on("click", CLUSTER_CIRCLE_ID, handleClusterClick);
    map.on("mouseenter", UNCLUSTERED_ID, setCursorPointer);
    map.on("mouseleave", UNCLUSTERED_ID, resetCursor);
    map.on("mouseenter", CLUSTER_CIRCLE_ID, setCursorPointer);
    map.on("mouseleave", CLUSTER_CIRCLE_ID, resetCursor);

    return () => {
      map.off("click", UNCLUSTERED_ID, handlePointClick);
      map.off("click", CLUSTER_CIRCLE_ID, handleClusterClick);
      map.off("mouseenter", UNCLUSTERED_ID, setCursorPointer);
      map.off("mouseleave", UNCLUSTERED_ID, resetCursor);
      map.off("mouseenter", CLUSTER_CIRCLE_ID, setCursorPointer);
      map.off("mouseleave", CLUSTER_CIRCLE_ID, resetCursor);
    };
  }, [isLoaded, map]);

  return null;
}
