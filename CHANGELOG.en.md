# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and this project follows [Semantic Versioning](https://semver.org/).

## [0.1.0] - 2026-03-05

### Added
- `GET /health` endpoint with checks for API, database, and Redis.
- Output connector framework (`services/output/`) with abstract base and
  connectors for Telegram, Discord, and webhooks.
- Frontend map components for detail and visualization (`AlertMap`, `AlertPopup`,
  `AlertDetailMap`, `ConnectionIndicator`, `AlertPolygonLayer`).
- Legal disclaimer about non-affiliation with Spain Government's ES-Alert system.

### Changed
- Pydantic schemas split into modules: `schemas/event.py`, `schemas/auth.py`, etc.
- Notification service migrated to output connector architecture.
- `reports.py` uses centralized schemas from `schemas/` (removes duplicates).
- README updated with bilingual description and governance links.
- CI expanded with PostGIS and Redis services for backend tests.

### Removed
- `MAPBOX_TOKEN` configuration (unused).

---

## [0.0.1] - 2026-03-03

### Added
- Ingestion of AEMET alerts (CAP XML), IGN (FDSN text), DGT (DATEX2 XML),
  MeteoAlarm (JSON/CAP).
- FastAPI REST API: events, JWT auth, subscriptions, collaborative reports, GDPR.
- Real-time alert WebSocket with Redis pub/sub.
- Next.js 15 frontend with MapLibre GL, shadcn/ui, Tailwind CSS.
- Meshtastic gateway (LoRa) for mesh communication.
- Docker Compose for development, deployment, and production.
- GitHub Actions for CI (lint + test) and SSH deployment.
- OSS Governance: LICENSE (AGPL-3.0), CODE_OF_CONDUCT, CONTRIBUTING,
  SECURITY, TRADEMARK_POLICY.
