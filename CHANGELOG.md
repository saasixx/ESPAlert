# Changelog

Todos los cambios notables de este proyecto se documentan en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/)
y este proyecto sigue [Semantic Versioning](https://semver.org/lang/es/).

## [Sin publicar]

### Añadido
- `ROADMAP.md` con plan de versiones v0.1 → v0.3.
- `CHANGELOG.md` siguiendo Keep a Changelog.
- Framework de conectores de salida (`services/output/`) con base abstracta, Telegram, Discord, email y webhook.
- Modelo `NotificationChannel` y `AlertSubscription` para suscripciones multi-canal.
- Capa de repositorios (`repositories/`) para separar lógica de acceso a datos.
- Servicio de caché Redis (`services/cache.py`) con invalidación por pub/sub.
- Tarea de limpieza (`tasks/cleanup.py`) para purgar eventos expirados.
- Endpoint `GET /health` ampliado con checks de DB, Redis, Celery y estado de ingesta.
- Logging estructurado JSON en producción, legible en desarrollo.
- Configuración de Prometheus + Grafana + Alertmanager (`monitoring/`).
- Migración del mapa a [mapcn](https://mapcn.dev): `AlertMap`, `AlertClusterLayer`, `AlertPolygonLayer`, `AlertMarker`.
- Nuevos componentes frontend: `AlertPopup`, `AlertDetail`, `ConnectionIndicator`, `FilterBar`.
- Hook `useEventsWS` mejorado con heartbeat y estados de conexión.
- Plantillas de issues: `data_source_request.md`, `connector_request.md`.
- Aviso legal de no afiliación con ES-Alert del Gobierno de España.

### Cambiado
- Esquemas Pydantic divididos en módulos: `schemas/event.py`, `schemas/auth.py`, etc.
- Servicio de notificaciones migrado a la arquitectura de conectores de salida.
- `reports.py` usa los esquemas centralizados de `schemas/` (elimina duplicados).
- README actualizado con descripción bilingüe y sección de screenshots.
- CI ampliada con servicios PostGIS y Redis para tests de integración.

### Eliminado
- Directorio `app_flutter_archive/` (stack móvil Flutter archivado).
- Configuración `MAPBOX_TOKEN` (no utilizada, se usa CARTO).
- Dependencia `react-map-gl` reemplazada por mapcn (MapLibre directo).

---

## [0.0.1] - 2026-03-03

### Añadido
- Ingesta de alertas AEMET (CAP XML), IGN (FDSN text), DGT (DATEX2 XML), MeteoAlarm (JSON/CAP).
- API REST con FastAPI: eventos, auth JWT, suscripciones, reportes colaborativos, RGPD.
- WebSocket de alertas en tiempo real con Redis pub/sub.
- Frontend Next.js 15 con MapLibre GL, shadcn/ui, Tailwind CSS.
- Gateway Meshtastic (LoRa) para comunicación mesh.
- Docker Compose para desarrollo, despliegue y producción.
- GitHub Actions para CI (lint + test) y deploy por SSH.
- Gobernanza OSS: LICENSE (AGPL-3.0), CODE_OF_CONDUCT, CONTRIBUTING, SECURITY, TRADEMARK_POLICY.
