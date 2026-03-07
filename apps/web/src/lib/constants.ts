/** Shared application constants. */

/** Severity colors indexed by level. */
export const SEVERITY_COLORS: Record<string, string> = {
  red: "#ef4444",
  orange: "#f97316",
  yellow: "#eab308",
  green: "#22c55e",
};

/** Polygon fill opacity by severity. */
export const SEVERITY_FILL_OPACITY: Record<string, number> = {
  red: 0.35,
  orange: 0.25,
  yellow: 0.18,
  green: 0.1,
};

/** Severity visual configuration for badges and UI. */
export const SEVERITY_CONFIG: Record<
  string,
  { color: string; label: string; labelEn: string }
> = {
  red: {
    color: "bg-red-500/20 text-red-500 border-red-500/50",
    label: "EXTREMO",
    labelEn: "EXTREME",
  },
  orange: {
    color: "bg-orange-500/20 text-orange-500 border-orange-500/50",
    label: "IMPORTANTE",
    labelEn: "SEVERE",
  },
  yellow: {
    color: "bg-yellow-500/20 text-yellow-500 border-yellow-500/50",
    label: "RIESGO",
    labelEn: "MODERATE",
  },
  green: {
    color: "bg-green-500/20 text-green-500 border-green-500/50",
    label: "SIN RIESGO",
    labelEn: "MINOR",
  },
};

/** Initial view centered on the Iberian Peninsula. */
export const SPAIN_CENTER: [number, number] = [-3.7, 40.0];
export const SPAIN_ZOOM = 5.5;
export const SPAIN_MIN_ZOOM = 4;
export const SPAIN_MAX_ZOOM = 18;

/** Map bounds (SW, NE) — covers Peninsula + Canary Islands + Balearic Islands. */
export const SPAIN_BOUNDS: [[number, number], [number, number]] = [
  [-19.0, 27.0], // SW
  [5.5, 44.5], // NE
];

/** Event categories with their icons and labels. */
export const CATEGORY_CONFIG: Record<
  string,
  { label: string; icon: string }
> = {
  meteo: { label: "Meteo", icon: "CloudRain" },
  seismic: { label: "Sismos", icon: "Activity" },
  traffic: { label: "Tráfico", icon: "Car" },
  maritime: { label: "Costero", icon: "Waves" },
};

/**
 * Resolves the display category from an event's icon_key hint (backend)
 * or falls back to deriving it from event_type.
 */
export function getEventCategory(
  eventType: string,
  iconKey?: string | null,
): string {
  if (iconKey && iconKey in CATEGORY_CONFIG) return iconKey;
  if (eventType.startsWith("traffic")) return "traffic";
  if (eventType === "earthquake" || eventType === "tsunami") return "seismic";
  if (["coastal", "wave", "tide"].includes(eventType)) return "maritime";
  return "meteo";
}
