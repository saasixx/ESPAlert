/**
 * Centroid coordinates [longitude, latitude] for Spanish provinces, islands,
 * and common sub-regional area names used by AEMET / MeteoAlarm.
 *
 * Used as a fallback to place markers on the map when events lack polygon geometry.
 */

const AREA_CENTROIDS: Record<string, [number, number]> = {
  // ── Canary Islands ─────────────────────────────────────────────────
  "lanzarote": [-13.63, 29.05],
  "fuerteventura": [-14.02, 28.40],
  "gran canaria": [-15.45, 27.96],
  "tenerife": [-16.55, 28.29],
  "la gomera": [-17.11, 28.10],
  "la palma": [-17.87, 28.68],
  "el hierro": [-18.00, 27.74],

  // ── Balearic Islands ────────────────────────────────────────────────
  "mallorca": [2.98, 39.62],
  "menorca": [4.08, 39.95],
  "ibiza": [1.43, 38.91],
  "formentera": [1.43, 38.70],

  // ── Autonomous cities ──────────────────────────────────────────────
  "ceuta": [-5.31, 35.89],
  "melilla": [-2.94, 35.29],

  // ── Provinces (by name) ────────────────────────────────────────────
  "a coruña": [-8.40, 43.37],
  "coruña": [-8.40, 43.37],
  "álava": [-2.67, 42.85],
  "albacete": [-1.86, 38.99],
  "alicante": [-0.49, 38.35],
  "almería": [-2.46, 36.84],
  "asturias": [-5.86, 43.36],
  "ávila": [-5.00, 40.66],
  "badajoz": [-6.97, 38.88],
  "barcelona": [2.17, 41.39],
  "bizkaia": [-2.93, 43.26],
  "burgos": [-3.70, 42.34],
  "cáceres": [-6.37, 39.47],
  "cádiz": [-6.29, 36.53],
  "cantabria": [-3.80, 43.18],
  "castellón": [-0.05, 39.99],
  "ciudad real": [-3.93, 38.99],
  "córdoba": [-4.78, 37.88],
  "cuenca": [-2.13, 40.07],
  "girona": [2.82, 41.98],
  "granada": [-3.60, 37.18],
  "guadalajara": [-3.17, 40.63],
  "gipuzkoa": [-2.17, 43.31],
  "huelva": [-6.95, 37.26],
  "huesca": [-0.41, 42.14],
  "jaén": [-3.79, 37.77],
  "león": [-5.57, 42.60],
  "lleida": [0.63, 41.62],
  "lugo": [-7.56, 43.01],
  "madrid": [-3.70, 40.42],
  "málaga": [-4.42, 36.72],
  "murcia": [-1.13, 37.99],
  "navarra": [-1.65, 42.82],
  "ourense": [-7.86, 42.34],
  "palencia": [-4.53, 42.01],
  "pontevedra": [-8.65, 42.43],
  "la rioja": [-2.45, 42.29],
  "salamanca": [-5.66, 40.97],
  "segovia": [-4.12, 40.95],
  "sevilla": [-5.99, 37.39],
  "soria": [-2.47, 41.76],
  "tarragona": [1.25, 41.12],
  "teruel": [-1.10, 40.35],
  "toledo": [-4.02, 39.86],
  "valencia": [-0.38, 39.47],
  "valladolid": [-4.72, 41.65],
  "zamora": [-5.75, 41.50],
  "zaragoza": [-0.88, 41.65],

  // ── Frequently alerted sub-regions ─────────────────────────────────
  "axarquía": [-4.10, 36.78],
  "sol y guadalhorce": [-4.60, 36.72],
  "costa granadina": [-3.50, 36.73],
  "poniente y almería capital": [-2.46, 36.84],
  "levante almeriense": [-1.90, 37.10],
  "guadix y baza": [-3.13, 37.30],
  "nevada y alpujarras": [-3.35, 36.96],
  "valle del almanzora y los vélez": [-2.10, 37.40],
  "estrecho": [-5.60, 36.00],

  "campo de cartagena y mazarrón": [-1.00, 37.60],
  "altiplano de murcia": [-1.40, 38.40],

  "cazorla y segura": [-2.90, 38.05],
  "alcaraz y segura": [-2.50, 38.60],
  "hellín y almansa": [-1.60, 38.70],
  "la mancha albaceteña": [-1.90, 39.00],
  "la mancha conquense": [-2.20, 39.50],
  "la mancha de ciudad real": [-3.60, 39.00],

  "sierra de madrid": [-3.80, 40.80],
  "sierra norte de sevilla": [-5.70, 37.90],
  "sierra y pedroches": [-4.60, 38.30],
  "sierras de alcudia y madrona": [-4.10, 38.55],
  "morena y condado": [-6.40, 37.70],
  "sur de badajoz": [-6.60, 38.40],

  "serranía de guadalajara": [-2.50, 40.80],
  "alcarria de guadalajara": [-2.80, 40.60],
  "gúdar y maestrazgo": [-0.70, 40.40],

  "pirineo de girona": [2.10, 42.35],
  "prelitoral de girona": [2.70, 41.90],
  "prelitoral sur de tarragona": [1.10, 41.00],
  "litoral norte de castellón": [0.02, 40.20],
  "litoral sur de castellón": [-0.05, 39.85],
  "interior norte de castellón": [-0.20, 40.30],
  "interior sur de castellón": [-0.30, 39.90],
  "interior de alicante": [-0.60, 38.60],
  "litoral norte de alicante": [-0.20, 38.60],
  "litoral sur de alicante": [-0.60, 38.20],
  "litoral sur de valencia": [-0.30, 39.10],
  "interior sur de valencia": [-0.80, 39.00],
  "litoral de barcelona": [2.17, 41.38],
  "litoral norte de tarragona": [1.30, 41.10],
  "litoral sur de tarragona": [0.80, 40.80],

  // ── Galicia (sub-zones) ────────────────────────────────────────────
  "a mariña": [-7.60, 43.40],
  "rias baixas": [-8.70, 42.30],
  "miño de pontevedra": [-8.60, 42.10],
  "noroeste de a coruña": [-8.80, 43.30],
  "oeste de a coruña": [-8.60, 43.00],
  "suroeste de a coruña": [-8.90, 42.80],

  // ── Canary Islands (sub-zones) ─────────────────────────────────────
  "norte de gran canaria": [-15.50, 28.10],
  "cumbres de gran canaria": [-15.55, 27.96],
  "este, sur y oeste de gran canaria": [-15.45, 27.85],
  "norte de tenerife": [-16.50, 28.42],
  "este, sur y oeste de tenerife": [-16.50, 28.15],
  "área metropolitana de tenerife": [-16.30, 28.46],
  "cumbres de la palma": [-17.85, 28.72],
  "este de la palma": [-17.78, 28.65],
  "oeste de la palma": [-17.92, 28.68],
};

/**
 * Resolve approximate centroid [lon, lat] for a given area_name.
 *
 * Strategy:
 * 1. Exact match (case-insensitive)
 * 2. Strip "Costa - " prefix and retry
 * 3. Partial match: check if any key is contained in the area name
 * 4. Return null if unresolvable
 */
export function resolveAreaCentroid(areaName: string | null | undefined): [number, number] | null {
  if (!areaName) return null;

  const normalised = areaName.toLowerCase().trim();

  // 1. Direct match
  if (AREA_CENTROIDS[normalised]) return AREA_CENTROIDS[normalised];

  // 2. Strip "Costa - " prefix
  const stripped = normalised.replace(/^costa\s*-\s*/, "");
  if (AREA_CENTROIDS[stripped]) return AREA_CENTROIDS[stripped];

  // 3. Partial match — check if area name contains a known key (prefer longest match)
  let bestMatch: [number, number] | null = null;
  let bestLen = 0;

  for (const [key, coords] of Object.entries(AREA_CENTROIDS)) {
    if (normalised.includes(key) && key.length > bestLen) {
      bestMatch = coords;
      bestLen = key.length;
    }
  }

  return bestMatch;
}
