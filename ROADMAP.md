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
| 2 | **Mapa interactivo con mapcn** | Migración de `react-map-gl` a [mapcn](https://mapcn.dev) con clustering, popups de detalle, filtros por categoría/severidad y modo oscuro. |
| 3 | **Vista detalle de alerta** | Página/modal `/alerts/:id` con geometría, instrucciones, fuente y timeline. |
| 4 | **Responsive mobile-first** | Sidebar como `Sheet`/`Drawer` en pantallas pequeñas, mapa full-screen. |
| 5 | **Health checks y CI robusta** | Endpoints `GET /health` detallado, tests de parsers con fixtures XML/CSV, CI con servicio PostGIS. |
| 6 | **Documentación mínima** | README con screenshots, `.env.example` completo, guía de desarrollo local. |

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
