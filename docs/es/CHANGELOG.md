# Changelog

> 🇪🇸 **Español** | [🇬🇧 English](../CHANGELOG.md)

Todos los cambios notables de este proyecto se documentan en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/)
y este proyecto sigue [Semantic Versioning](https://semver.org/lang/es/).

## [0.1.0] - 2026-03-05

### Añadido
- Endpoint `GET /health` con checks de API, base de datos y Redis.
- Framework de conectores de salida (`services/output/`) con base abstracta y conectores de Telegram, Discord y webhook.
- Componentes de mapa en frontend para detalle y visualización (`AlertMap`, `AlertPopup`, `AlertDetailMap`, `ConnectionIndicator`, `AlertPolygonLayer`).
- Aviso legal de no afiliación con ES-Alert del Gobierno de España.

### Cambiado
- Esquemas Pydantic divididos en módulos: `schemas/event.py`, `schemas/auth.py`, etc.
- Servicio de notificaciones migrado a la arquitectura de conectores de salida.
- `reports.py` usa los esquemas centralizados de `schemas/` (elimina duplicados).
- README actualizado con descripción bilingüe y enlaces de gobernanza.
- CI ampliada con servicios PostGIS y Redis para tests backend.

### Eliminado
- Configuración `MAPBOX_TOKEN` (no utilizada).

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
