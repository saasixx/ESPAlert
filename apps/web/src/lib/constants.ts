/** Constantes compartidas de la aplicación. */

/** Colores de severidad indexados por nivel. */
export const SEVERITY_COLORS: Record<string, string> = {
  red: "#ef4444",
  orange: "#f97316",
  yellow: "#eab308",
  green: "#22c55e",
};

/** Opacidad de relleno de polígonos por severidad. */
export const SEVERITY_FILL_OPACITY: Record<string, number> = {
  red: 0.35,
  orange: 0.25,
  yellow: 0.18,
  green: 0.1,
};

/** Configuración visual de severidad para badges y UI. */
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

/** Vista inicial centrada en la Península Ibérica. */
export const SPAIN_CENTER: [number, number] = [-3.7, 40.0];
export const SPAIN_ZOOM = 5.5;
export const SPAIN_MIN_ZOOM = 4;
export const SPAIN_MAX_ZOOM = 18;

/** Límites del mapa (SW, NE) — cubre Península + Canarias + Baleares. */
export const SPAIN_BOUNDS: [[number, number], [number, number]] = [
  [-19.0, 27.0], // SW
  [5.5, 44.5], // NE
];

/** Categorías de eventos con sus iconos y labels. */
export const CATEGORY_CONFIG: Record<
  string,
  { label: string; icon: string }
> = {
  meteo: { label: "Meteo", icon: "CloudRain" },
  seismic: { label: "Sismos", icon: "Activity" },
  traffic: { label: "Tráfico", icon: "Car" },
  maritime: { label: "Costero", icon: "Waves" },
};
