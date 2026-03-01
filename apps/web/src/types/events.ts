export interface AlertEvent {
  id: string;
  source: string;
  source_id: string;
  event_type: string;
  severity: string;
  title: string;
  description?: string | null;
  instructions?: string | null;
  area_name?: string | null;
  area_geojson?: any;
  effective?: string | null;
  expires?: string | null;
  source_url?: string | null;
  magnitude?: string | null;
  depth_km?: string | null;
  created_at: string;
}

export type EventCategory = 'meteo' | 'seismic' | 'traffic' | 'maritime';
