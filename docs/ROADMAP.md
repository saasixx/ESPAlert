# ESPAlert Roadmap

> 🇬🇧 **English** | [🇪🇸 Español](es/ROADMAP.md)

This document describes the ESPAlert development plan organized in incremental
releases. Each version has a clear goal, concrete epics, and completion criteria.

> **Versioning Convention**: we follow [Semantic Versioning 2.0](https://semver.org/).
> `PATCH` = bugfix / dependency update.
> `MINOR` = new feature without breaking the API.
> `MAJOR` = breaking change in REST or WebSocket API.

---

## v0.1.0 — "Live Map" (Public MVP)

**Goal**: first functional release with interactive map, ingestion from
4 official sources, and real-time WebSocket streaming.

### Epics

| # | Epic | Description |
|---|------|-------------|
| 1 | **Stable Ingestion** | Celery tasks (AEMET, IGN, DGT, MeteoAlarm) with retries, structured logs, and deduplication verified by tests. |
| 2 | **Interactive Map with mapcn** | Uses [mapcn](https://github.com/AnmolSaini16/mapcn) components with clustering, detail popups, category/severity filters, and dark mode support with next-themes. |
| 3 | **Alert Detail View** | Page/modal `/alerts/:id` with geometry, instructions, source, and timeline. |
| 4 | **Responsive Mobile-First** | Sidebar as `Sheet`/`Drawer` on small screens, full-screen map. |
| 5 | **Health Checks and Robust CI** | Detailed `GET /health` endpoint, parser tests with XML/CSV fixtures, CI with PostGIS service. |
| 6 | **Minimal Documentation** | README, complete `.env.example`, local development guide. |

### Done Criteria

- `docker compose up` starts the entire platform in < 2 min.
- Tests pass in CI (lint + backend + frontend).
- Map displays real AEMET + IGN alerts with live data.
- WebSocket delivers events to frontend in < 3 s from ingestion.
- Lighthouse mobile score ≥ 80.

---

## v0.2.0 — "Personalized Alerts"

**Goal**: registered users with zones of interest, filters, and multi-channel notifications.

### Epics

| # | Epic | Description |
|---|------|-------------|
| 1 | **Auth UI** | Login/register/profile pages in frontend with shadcn/ui forms. |
| 2 | **Zones and Map Filters** | Draw polygon on map → save as `UserZone`, create visual filters. |
| 3 | **Output Connectors** | Telegram bot, Discord webhook, email (SMTP), generic webhook with HMAC signature. Jinja2 template system. |
| 4 | **Collaborative Reports UI** | UI to send geolocated reports, report feed on map as additional layer. |
| 5 | **Redis Caching** | Cache `GET /events/` and `/active/summary` with invalidation via pub/sub when normalizing new events. |
| 6 | **Cleanup Task** | Purge events older > 30 days, archive to `events_archive` table. |
| 7 | **Contextual Iconography** | Custom icons on map by source (AEMET, IGN, DGT, MeteoAlarm), event type (weather, seismic, traffic, fires), and severity. Use `iconKey` in event payload to map to Leaflet `DivIcon` icons in mapcn, with consistent fallback. |
| 8 | **DGT Road Segments on Map** | For DGT incidents affecting roads (closures, congestion, construction), store optional `LineString` `segment` with affected section and draw as polyline on map, synchronized with event popup. |

### Done Criteria

- A user can register, create a zone in Madrid, add an `severity >= orange` filter,
  and receive a Telegram notification when an alert is published in their zone.
- Integration tests with PostGIS in CI.
- Map displays differentiated icons by domain (weather, earthquakes, traffic, fires)
  and severity without opening popups to understand alert context.
- For a DGT road closure incident, the map shows the affected section as a line
  on the road, and the event popup clearly indicates the section (road + start/end KM).

---

## v0.3.0 — "Open Platform"

**Goal**: public API documentation, Flutter app, observability, and first
community of external contributors.

### Epics

| # | Epic | Description |
|---|------|-------------|
| 1 | **Flutter App** | Mobile client with map, list, detail, and push notifications (FCM). |
| 2 | **API Docs OpenAPI** | Exported spec, Swagger UI, and ReDoc accessible at `/docs`. |
| 3 | **Observability** | Prometheus + Grafana + Alertmanager for ingestion, API, and Celery metrics. |
| 4 | **i18n** | English/Spanish support in frontend (`next-intl`) and API messages. |
| 5 | **PWA** | Service Worker for offline caching of base map and latest alerts. |
| 6 | **Public Webhooks** | API to register external webhooks with HMAC signature. |

### Done Criteria

- Flutter app on Google Play (open beta).
- Grafana dashboard with ≥ 10 metric panels.
- ≥ 5 external contributors with merged PRs.

---

## Beyond v0.3

Ideas for future versions (not prioritized):

- Risk prediction with ML (historical AEMET + IGN data).
- Integration with Civil Protection (official ES-Alert system).
- Multi-country support (Portugal, France, Italy).
- GraphQL API as alternative to REST.

---

## Proposed Future APIs

List of investigated public data sources that could be integrated into
ESPAlert as new connectors. Classified by domain.

### Meteorology and Climate (AEMET OpenData Extensions)

| API | Base Endpoint | Description | Priority |
|-----|---------------|-------------|----------|
| **AEMET — Fire Indexes** | `GET /api/incendios/mapasriesgo/estimado/area/{area}` | Meteorological wildfire risk maps (estimated and forecast). | High |
| **AEMET — Lightning Network** | `GET /api/red/rayos/mapa` | Real-time lightning strike impacts; useful for thunderstorms. | Medium |
| **AEMET — UVI (Ultraviolet)** | `GET /api/prediccion/especifica/uvi/{dia}` | Daily UV radiation forecast by zone. | Low |
| **AEMET — Nivology / Avalanches** | `GET /api/prediccion/especifica/nivologica/{area}` | Snowpack and avalanche risk in mountain areas. | Medium |
| **AEMET — Beach Forecast** | `GET /api/prediccion/especifica/playa/{playa}` | Beach conditions and forecast; swell, wind, UV. | Low |
| **AEMET — National Radar** | `GET /api/red/radar/nacional` | National radar composite of precipitation in real-time. | Medium |
| **AEMET — Background Pollution** | `GET /api/red/especial/contaminacionfondo/estacion/{nombre}` | Background air pollution monitoring station data. | Low |

> **Note:** All AEMET endpoints require the same API key already used for CAP alerts (`opendata.aemet.es`).

### Hydrology and Flooding

| API | URL | Description | Priority |
|-----|-----|-------------|----------|
| **EFAS — European Flood Awareness System** | `european-flood.emergency.copernicus.eu` | Fluvial flood alerts across Europe, with discharge forecast levels and risk maps. Free access via Copernicus account. | High |
| **SAIH — Automatic Hydrological Information System** | Varies by Confederation (Ebro, Tajo, Guadalquivir…) | Real-time river level, reservoir, and rainfall data. Each confederation publishes SAIH portals; may require scraping or API negotiation. | Medium |

### Forest Fires

| API | URL | Description | Priority |
|-----|-----|-------------|----------|
| **EFFIS — European Forest Fire Information System** | `maps.effis.emergency.copernicus.eu/effis` (WFS/WMS) | Active hotspot detection (MODIS/VIIRS), burned area perimeters, and Fire Weather Index. Data downloadable as Shapefile/SpatiaLite via WFS. | High |
| **AEMET — Fire Indexes** | See Meteorology section | Meteorological fire risk by zone. | High |

### Volcanic and Seismic Activity (IGN Extensions)

| API | URL | Description | Priority |
|-----|-----|-------------|----------|
| **IGN — Volcano Catalog** | `www.ign.es/web/resources/volcanologia/` | Volcanic monitoring info for Canary Islands (La Palma, El Hierro, Tenerife). No formal REST API; likely requires scraping seismic data + press releases. | Medium |
| **CSIC / INVOLCAN** | `involcan.com` | Canary Islands Volcanological Institute; volcanic activity data and bulletins. | Low |

### Energy

| API | URL | Description | Priority |
|-----|-----|-------------|----------|
| **Red Eléctrica (REE) — REData API** | `apidatos.ree.es/es/datos/{category}/{widget}` | Real-time demand, generation, and electrical balance data. Helps detect demand peaks or grid stress. Public REST API, JSON, no authentication. | Medium |

### Maritime and Oceanographic

| API | URL | Description | Priority |
|-----|-----|-------------|----------|
| **Puertos del Estado — PORTUS** | `portus.puertos.es` | Ocean buoy network, tide gauges, and HF radar. Real-time swell, sea level, water temperature, and current data. | Medium |
| **AEMET — Maritime Forecast** | `GET /api/prediccion/maritima/costera/costa/{costa}` | Swell and wind forecast for coasts and open sea. | Medium |

### Air Quality

| API | URL | Description | Priority |
|-----|-----|-------------|----------|
| **MITECO — Monitoring Network** | `www.miteco.gob.es` (air quality evaluation and data) | National air quality monitoring stations: PM10, PM2.5, NO₂, O₃, SO₂. Some autonomous communities publish their own APIs (Madrid, Barcelona, Basque Country). | Medium |
| **European Air Quality Index** | `airindex.eea.europa.eu` | Consolidated European Environment Agency data with Spain coverage. | Low |

### Civil Protection and Emergencies

| API | URL | Description | Priority |
|-----|-----|-------------|----------|
| **DGPCE — Directorate General of Civil Protection** | `www.proteccioncivil.es` | Official ES-Alert system alerts (Cell Broadcast EU). Currently no formal public API; could monitor via RSS/scraping press releases. | High |
| **Generalitat de Catalunya — Civil Protection** | `datos.gob.es` (open dataset) | Active civil protection plans (pre-alert, alert, emergency). CSV/JSON available on datos.gob.es. | Medium |
| **Copernicus EMS — Rapid Mapping** | `emergency.copernicus.eu/mapping` | Rapid disaster cartography (floods, earthquakes, fires). Activations with vector maps. | Low |

### Criteria for Adding a New Source

1. **Open or Free Data** — Prioritize free/open APIs.
2. **Structured Format** — JSON, XML, CAP, GeoJSON, WFS; avoid PDFs.
3. **Frequent Updates** — Minimum hourly for live alerts.
4. **National Coverage** — Prefer sources covering all of Spain.
5. **Geolocation** — Data with coordinates or polygons for mapping.
