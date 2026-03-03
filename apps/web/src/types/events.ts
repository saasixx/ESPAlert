/** Evento de alerta devuelto por la API. */
export interface AlertEvent {
  id: string;
  source: string;
  source_id: string;
  event_type: string;
  severity: "green" | "yellow" | "orange" | "red";
  title: string;
  description?: string | null;
  instructions?: string | null;
  area_name?: string | null;
  area_geojson?: GeoJSON.Geometry | null;
  effective?: string | null;
  expires?: string | null;
  source_url?: string | null;
  magnitude?: string | null;
  depth_km?: string | null;
  created_at: string;
}

/** Categorías de eventos para los filtros del mapa. */
export type EventCategory = "meteo" | "seismic" | "traffic" | "maritime";
