<p align="center">
  <img src="apps/web/public/espalert-logo.svg" alt="ESPAlert Logo" width="120" />
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Next.js-16-black?logo=next.js" alt="Next.js 16" />
  <img src="https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi" alt="FastAPI" />
  <img src="https://img.shields.io/badge/PostGIS-16-336791?logo=postgresql" alt="PostGIS" />
  <img src="https://img.shields.io/badge/MapLibre_GL-5-blue?logo=maplibre" alt="MapLibre" />
  <img src="https://img.shields.io/badge/License-AGPLv3-green" alt="AGPLv3 License" />
  <img src="https://img.shields.io/github/actions/workflow/status/saasixx/ESPAlert/ci.yml?branch=main&label=CI" alt="CI" />
  <img src="https://img.shields.io/github/actions/workflow/status/saasixx/ESPAlert/deploy.yml?branch=main&label=Deploy" alt="Deploy" />
  <img src="https://img.shields.io/badge/PRs-welcome-brightgreen.svg" alt="PRs Welcome" />
  <img src="https://img.shields.io/badge/Docker-ready-2496ED?logo=docker" alt="Docker Ready" />
</p>

# ESPAlert

> 🇬🇧 **English** | [🇪🇸 Español](docs/es/README.md)

**Multi-risk real-time alert system for Spain**

ESPAlert is an **Open Source** platform that aggregates weather, earthquake,
traffic, and civil protection alerts into a single interactive map focused on
Spain. It consumes public data from official Spanish and European sources (AEMET,
IGN, DGT, MeteoAlarm) and delivers real-time updates via REST API and WebSockets.

> ⚠️ **Legal Notice**: ESPAlert is an independent Open Source community project.
> **It is not affiliated, sponsored, or linked in any way with the Spain
> Government's ES-Alert system** or the Directorate General of Civil Protection
> and Emergencies. ESPAlert consumes exclusively open public data published by
> AEMET, IGN, DGT, and MeteoAlarm under their respective licenses. The name
> "ESPAlert" refers to "España + Alertas" and does not intend to create
> confusion with ES-Alert.

<p align="center">
  <a href="docs/ROADMAP.md">Roadmap</a> ·
  <a href="docs/CHANGELOG.md">Changelog</a> ·
  <a href="CONTRIBUTING.md">Contributing</a> ·
  <a href="SECURITY.md">Security</a> ·
  <a href="docs/TRADEMARK_POLICY.md">Trademark</a> ·
  <a href=".github/ISSUE_TEMPLATE/bug_report.md">Report Bug</a> ·
  <a href="DOCS.md">📚 Bilingual Docs</a> ·
  <a href="docs/es/README.md">📖 Español</a>
</p>

<p align="center">
  <em>Interactive Map · Live WebSockets · Meshtastic LoRa · GDPR/LOPDGDD</em>
</p>

---

## Table of Contents

- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Local Development](#local-development)
- [Data Sources](#data-sources)
- [Environment Variables](#environment-variables)
- [Production Deployment](#production-deployment)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [License](#license)

---

## Architecture

```text
┌──────────────────────────────────────────────────────────────┐
│                        Turborepo                             │
│                                                              │
│  ┌──────────────┐    WebSocket / REST    ┌────────────────┐  │
│  │  apps/web    │◄──────────────────────►│   apps/api     │  │
│  │  Next.js 16  │                        │   FastAPI      │  │
│  │  MapLibre GL │                        │   Celery       │  │
│  │  shadcn/ui   │                        │   PostGIS      │  │
│  └──────────────┘                        └───────┬────────┘  │
│                                              │   │   │       │
│                              ┌───────────────┘   │   └──┐    │
│                              ▼                   ▼      ▼    │
│                         PostgreSQL            Redis  Mesh GW │
│                         + PostGIS                    (LoRa)  │
└──────────────────────────────────────────────────────────────┘
```

| Component        | Technology                                    | Location           |
|------------------|-----------------------------------------------|--------------------|
| **Web Frontend** | Next.js 16, Tailwind CSS, shadcn/ui, MapLibre | `apps/web`         |
| **API Backend**  | Python 3.12, FastAPI, PostGIS, Celery, Redis  | `apps/api`         |
| **Monorepo**     | Turborepo + npm workspaces                    | Root               |
| **Mesh Radio**   | Meshtastic (LoRa)                             | `apps/api/connectors` |

## Quick Start

> **Requirements**: [Docker](https://docs.docker.com/get-docker/) 24+ and
> [Node.js](https://nodejs.org/) 20 LTS.

```bash
# 1. Clone the repository
git clone https://github.com/saasixx/ESPAlert.git
cd ESPAlert

# 2. Configure environment variables
cp .env.example .env
# Adjust AEMET_API_KEY if you have one (free)

# 3. Start the entire platform
docker compose up --build
```

| Service      | URL                         |
|--------------|----------------------------|
| **Web App**  | http://localhost:3000       |
| **API REST** | http://localhost:8000       |
| **Swagger**  | http://localhost:8000/docs  |

## Local Development

If you prefer to run the frontend outside Docker (faster hot-reload):

```bash
# Start only infrastructure + backend
docker compose up db redis api worker beat -d

# Install monorepo dependencies
npm install

# Start frontend with Turborepo
npm run dev
```

## Data Sources

| Source        | Type             | Frequency | Format      |
|---------------|------------------|-----------|-------------|
| AEMET OpenData | Weather alerts   | 5 min     | CAP XML     |
| IGN FDSN      | Earthquakes      | 2 min     | Text/CSV    |
| DGT NAP       | Traffic          | 5 min     | DATEX2 XML  |
| MeteoAlarm    | European alerts  | 5 min     | GeoJSON/CAP |

## Environment Variables

Copy `.env.example` to `.env` and adjust values. Key variables:

| Variable             | Description                              | Required |
|----------------------|------------------------------------------|----------|
| `DATABASE_URL`       | PostgreSQL connection (asyncpg)          | Yes      |
| `REDIS_URL`          | Redis connection                         | Yes      |
| `AEMET_API_KEY`      | [AEMET OpenData][aemet] key (free)       | No*      |
| `JWT_SECRET`         | Secret for JWT tokens (≥32 chars)        | Prod     |
| `ALLOWED_ORIGINS`    | Allowed CORS origins                     | Prod     |

> \* Without AEMET key, weather alerts won't be available, but other sources
> (IGN, DGT, MeteoAlarm) work without authentication.

[aemet]: https://opendata.aemet.es/centrodedescargas/inicio

## Production Deployment

```bash
# On the server:
git clone https://github.com/saasixx/ESPAlert.git /opt/espalert
cd /opt/espalert
cp .env.example .env
# Edit .env with real production values!

docker compose up -d --build
```

The repository includes GitHub Actions in `.github/workflows/` for CI and
automatic SSH deployment. Configure repository secrets:

- `SERVER_HOST` — Server IP or domain.
- `SERVER_USER` — SSH user.
- `SERVER_SSH_KEY` — Private SSH key.

## Roadmap

Check [ROADMAP.md](docs/ROADMAP.md) for the development plan and upcoming
releases. Published changes are recorded in [CHANGELOG.md](docs/CHANGELOG.md).

| Version  | Goal | Status |
|----------|------|--------|
| **v0.1.0** | Public MVP — interactive map + ingestion + WebSocket | 🚧 In Development |
| **v0.2.0** | Personalized Alerts — zones, filters, notifications | 📋 Planned |
| **v0.3.0** | Open Platform — Flutter app, observability, i18n | 📋 Planned |

## Contributing

Contributions are welcome! Read [CONTRIBUTING.md](CONTRIBUTING.md)
for the workflow, conventions, and how to send a Pull Request.

**New to the project?** Look for issues with the
[`good first issue`](../../issues?q=label%3A%22good+first+issue%22) label — small, well-defined tasks for beginners.

This project follows the [Contributor Code of Conduct](CODE_OF_CONDUCT.md).

## Security

If you discover a vulnerability, **do not open a public issue**. See
[SECURITY.md](SECURITY.md) for responsible disclosure.

## Credits and Dependencies

ESPAlert is built on quality free software:

- **mapcn** — React components for MapLibre GL (MIT)
- **MapLibre GL** — Interactive map engine (BSD-3-Clause)
- **FastAPI** — Asynchronous web framework (MIT)
- **PostgreSQL + PostGIS** — Geospatial database (PostgreSQL License)
- **Next.js** — React framework with SSR (MIT)
- **Tailwind CSS** — CSS utilities (MIT)
- **shadcn/ui** — UI components (MIT)
- **Redis** — In-memory cache (BSD-3-Clause)
- **Celery** — Distributed task queue (BSD)

Special thanks to [AnmolSaini16](https://github.com/AnmolSaini16/) for mapcn
and to all the Open Source projects that make ESPAlert possible.

## License

Distributed under the **GNU AGPL-3.0-or-later** license. See [LICENSE](LICENSE).

To protect the project's identity, the name **ESPAlert**, its logo, and
brand elements are subject to a separate trademark policy.
See [TRADEMARK_POLICY.md](docs/TRADEMARK_POLICY.md).
