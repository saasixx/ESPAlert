# Roadmap ESPAlert

Este documento describe el plan de desarrollo de ESPAlert organizado en
releases incrementales. Cada versión tiene un objetivo claro, épicas
concretas y criterios de finalización.

> **Convención de versionado**: seguimos [Semantic Versioning 2.0](https://semver.org/lang/es/).
> `PATCH` = bugfix / actualización de dependencias.
> `MINOR` = nueva feature sin romper la API.
> `MAJOR` = breaking change en la API REST o WebSocket.

---

## v0.1.0 — "Mapa Vivo" (MVP público)

**Objetivo**: primera release funcional con mapa interactivo, ingesta de las
4 fuentes oficiales y streaming WebSocket en tiempo real.

### Épicas

| # | Épica | Descripción |
|---|-------|-------------|
| 1 | **Ingesta estable** | Tareas Celery (AEMET, IGN, DGT, MeteoAlarm) con reintentos, logs estructurados y deduplicación verificada por tests. |
| 2 | **Mapa interactivo con mapcn** | Utiliza componentes de [mapcn](https://github.com/AnmolSaini16/mapcn) con clustering, popups de detalle, filtros por categoría/severidad y soporte dark mode integrado con next-themes. |
| 3 | **Vista detalle de alerta** | Página/modal `/alerts/:id` con geometría, instrucciones, fuente y timeline. |
| 4 | **Responsive mobile-first** | Sidebar como `Sheet`/`Drawer` en pantallas pequeñas, mapa full-screen. |
| 5 | **Health checks y CI robusta** | Endpoints `GET /health` detallado, tests de parsers con fixtures XML/CSV, CI con servicio PostGIS. |
| 6 | **Documentación mínima** | README, `.env.example` completo, guía de desarrollo local. |

### Criterios de Done

- `docker compose up` levanta toda la plataforma en < 2 min.
- Tests pasan en CI (lint + backend + frontend).
- El mapa muestra alertas reales de AEMET + IGN con datos en vivo.
- WebSocket entrega eventos al frontend en < 3 s desde la ingesta.
- Lighthouse mobile score ≥ 80.

---

## v0.2.0 — "Alertas Personalizadas"

**Objetivo**: usuarios registrados con zonas de interés, filtros y
notificaciones multi-canal.

### Épicas

| # | Épica | Descripción |
|---|-------|-------------|
| 1 | **Auth UI** | Páginas de login/registro/perfil en el frontend con formularios shadcn/ui. |
| 2 | **Zonas y filtros en el mapa** | Dibujar polígono en el mapa → guardar como `UserZone`, crear filtros visuales. |
| 3 | **Conectores de salida** | Telegram bot, Discord webhook, email (SMTP), webhook genérico con firma HMAC. Sistema de plantillas Jinja2. |
| 4 | **Informes colaborativos UI** | UI para enviar reportes geolocalizados, feed en el mapa como capa adicional. |
| 5 | **Caché Redis** | Cachear `GET /events/` y `/active/summary` con invalidación por pub/sub al normalizar nuevos eventos. |
| 6 | **Tarea de limpieza** | Purga de eventos expirados > 30 días, archivado en tabla `events_archive`. |

### Criterios de Done

- Un usuario puede registrarse, crear una zona en Madrid, añadir un filtro
  `severity >= orange`, y recibir una notificación Telegram cuando se publique
  una alerta dentro de su zona.
- Tests de integración con PostGIS en CI.

---

## v0.3.0 — "Plataforma Abierta"

**Objetivo**: API pública documentada, app Flutter, observabilidad y primera
comunidad de contribuidores.

### Épicas

| # | Épica | Descripción |
|---|-------|-------------|
| 1 | **App Flutter** | Cliente móvil con mapa, lista, detalle y push notifications (FCM). |
| 2 | **API docs OpenAPI** | Spec exportada, Swagger UI y ReDoc accesibles en `/docs`. |
| 3 | **Observabilidad** | Prometheus + Grafana + Alertmanager para métricas de ingesta, API y Celery. |
| 4 | **i18n** | Soporte inglés/español en frontend (`next-intl`) y en mensajes de API. |
| 5 | **PWA** | Service Worker para caché offline del mapa base y últimas alertas. |
| 6 | **Webhooks públicos** | API para registrar webhooks externos con firma HMAC. |

### Criterios de Done

- App Flutter en Google Play (beta abierta).
- Dashboard Grafana con ≥ 10 paneles de métricas.
- ≥ 5 contribuidores externos con PRs mergeados.

---

## Más allá de v0.3

Ideas para versiones futuras (sin priorizar):

- Predicción de riesgo con ML (datos históricos de AEMET + IGN).
- Integración con Protección Civil (sistema ES-Alert oficial).
- Soporte multi-país (Portugal, Francia, Italia).
- API GraphQL como alternativa a REST.

---

## Propuestas de APIs futuras

Listado de fuentes de datos públicas investigadas que podrían integrarse a
ESPAlert como nuevos conectores. Clasificadas por dominio.

### Meteorología y clima (extensiones de AEMET OpenData)

| API | Endpoint base | Descripción | Prioridad |
|-----|---------------|-------------|-----------|
| **AEMET — Índices de incendios** | `GET /api/incendios/mapasriesgo/estimado/area/{area}` | Mapas de riesgo meteorológico de incendios forestales (estimado y previsto). | Alta |
| **AEMET — Red de Rayos** | `GET /api/red/rayos/mapa` | Registro de impactos de rayos en tiempo real; útil para tormentas eléctricas. | Media |
| **AEMET — UVI (ultravioleta)** | `GET /api/prediccion/especifica/uvi/{dia}` | Predicción diaria de radiación UV por zonas. | Baja |
| **AEMET — Nivología / avalanchas** | `GET /api/prediccion/especifica/nivologica/{area}` | Información nivológica y riesgo de avalanchas en zonas de montaña. | Media |
| **AEMET — Predicción playas** | `GET /api/prediccion/especifica/playa/{playa}` | Estado y predicción para playas; oleaje, viento, UV. | Baja |
| **AEMET — Radar nacional** | `GET /api/red/radar/nacional` | Composición radar de precipitación a nivel nacional en tiempo real. | Media |
| **AEMET — Contaminación de fondo** | `GET /api/red/especial/contaminacionfondo/estacion/{nombre}` | Datos de estaciones de contaminación atmosférica de fondo. | Baja |

> **Nota:** Todos los endpoints de AEMET requieren la misma API key que ya
> usamos para avisos CAP (`opendata.aemet.es`).

### Hidrología e inundaciones

| API | URL | Descripción | Prioridad |
|-----|-----|-------------|-----------|
| **EFAS — European Flood Awareness System** | `european-flood.emergency.copernicus.eu` | Alertas de inundación fluvial en toda Europa, con niveles de previsión de caudal y mapas de riesgo. Acceso gratuito previa solicitud de cuenta Copernicus. | Alta |
| **SAIH — Sistema Automático de Información Hidrológica** | Varía por Confederación (Ebro, Tajo, Guadalquivir…) | Datos en tiempo real de nivel de ríos, embalses y pluviometría. Cada confederación publica los datos en su portal SAIH; requiere scraping o negociar acceso API. | Media |

### Incendios forestales

| API | URL | Descripción | Prioridad |
|-----|-----|-------------|-----------|
| **EFFIS — European Forest Fire Information System** | `maps.effis.emergency.copernicus.eu/effis` (WFS/WMS) | Detección de puntos calientes activos (MODIS/VIIRS), perímetros de áreas quemadas y Fire Weather Index. Datos descargables como Shapefile / SpatiaLite vía WFS. | Alta |
| **AEMET — Índices de incendios** | Ver sección Meteorología | Riesgo meteorológico de incendio por zonas. | Alta |

### Actividad volcánica y sísmica (extensiones de IGN)

| API | URL | Descripción | Prioridad |
|-----|-----|-------------|-----------|
| **IGN — Catálogo volcánico** | `www.ign.es/web/resources/volcanologia/` | Información de vigilancia volcánica en Canarias (La Palma, El Hierro, Tenerife). No tiene API REST formal; probablemente requiere scraping de datos sísmicos + comunicados. | Media |
| **CSIC / INVOLCAN** | `involcan.com` | Instituto Volcanológico de Canarias; datos y boletines sobre actividad volcánica. | Baja |

### Energía

| API | URL | Descripción | Prioridad |
|-----|-----|-------------|-----------|
| **Red Eléctrica (REE) — REData API** | `apidatos.ree.es/es/datos/{category}/{widget}` | Datos de demanda, generación y balance eléctrico en tiempo real. Permite detectar picos de demanda o situaciones de estrés en la red. API REST pública, JSON, sin autenticación. | Media |

### Marítimo y oceanográfico

| API | URL | Descripción | Prioridad |
|-----|-----|-------------|-----------|
| **Puertos del Estado — PORTUS** | `portus.puertos.es` | Red de boyas oceánicas, mareógrafos y radares HF. Datos de oleaje, nivel del mar, temperatura del agua y corrientes en tiempo real. | Media |
| **AEMET — Predicción marítima** | `GET /api/prediccion/maritima/costera/costa/{costa}` | Predicción de oleaje y viento para costas y alta mar. | Media |

### Calidad del aire

| API | URL | Descripción | Prioridad |
|-----|-----|-------------|-----------|
| **MITECO — Red de vigilancia** | `www.miteco.gob.es` (evaluación y datos de calidad del aire) | Red nacional de estaciones de calidad del aire: PM10, PM2.5, NO₂, O₃, SO₂. Algunas CCAA publican APIs propias (Madrid, Barcelona, País Vasco). | Media |
| **European Air Quality Index** | `airindex.eea.europa.eu` | Datos consolidados de la Agencia Europea del Medio Ambiente con cobertura española. | Baja |

### Protección Civil y emergencias

| API | URL | Descripción | Prioridad |
|-----|-----|-------------|-----------|
| **DGPCE — Dirección General de Protección Civil** | `www.proteccioncivil.es` | Alertas oficiales del sistema ES-Alert (Cell Broadcast EU). Actualmente no tiene API pública formal; se podría monitorizar vía RSS/scraping de comunicados. | Alta |
| **Generalitat de Catalunya — Protecció Civil** | `datos.gob.es` (dataset abierto) | Planes de protección civil activos (prealerta, alerta, emergencia). Formato CSV/JSON accesible en datos.gob.es. | Media |
| **Copernicus EMS — Rapid Mapping** | `emergency.copernicus.eu/mapping` | Cartografía rápida de desastres (inundaciones, terremotos, incendios). Activaciones con mapas vectoriales. | Baja |

### Criterios para incorporar una nueva fuente

1. **Datos abiertos o gratuitos** — Priorizar APIs sin coste.
2. **Formato estructurado** — JSON, XML, CAP, GeoJSON, WFS; evitar PDFs.
3. **Actualización frecuente** — Mínimo cada hora para alertas en vivo.
4. **Cobertura nacional** — Preferir fuentes que cubran toda España.
5. **Geolocalización** — Datos con coordenadas o polígonos para mapear.
