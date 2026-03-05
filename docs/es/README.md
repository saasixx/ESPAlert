<p align="center">
  <img src="../../apps/web/public/espalert-logo.svg" alt="ESPAlert Logo" width="120" />
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Next.js-16-black?logo=next.js" alt="Next.js 16" />
  <img src="https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi" alt="FastAPI" />
  <img src="https://img.shields.io/badge/PostGIS-16-336791?logo=postgresql" alt="PostGIS" />
  <img src="https://img.shields.io/badge/MapLibre_GL-5-blue?logo=maplibre" alt="MapLibre" />
  <img src="https://img.shields.io/badge/Licencia-AGPLv3-green" alt="AGPLv3 License" />
  <img src="https://img.shields.io/github/actions/workflow/status/saasixx/ESPAlert/ci.yml?branch=main&label=CI" alt="CI" />
  <img src="https://img.shields.io/github/actions/workflow/status/saasixx/ESPAlert/deploy.yml?branch=main&label=Deploy" alt="Deploy" />
  <img src="https://img.shields.io/badge/PRs-welcome-brightgreen.svg" alt="PRs Welcome" />
  <img src="https://img.shields.io/badge/Docker-ready-2496ED?logo=docker" alt="Docker Ready" />
</p>

# ESPAlert

**Sistema de alertas multi-riesgo en tiempo real para España**

> 🇪🇸 **Español** | [🇬🇧 English](../../README.md)

🇪🇸 ESPAlert es una plataforma **Open Source** que agrega alertas de
meteorología, sismos, tráfico y protección civil en un único mapa interactivo
centrado en España. Consume datos públicos de AEMET, IGN, DGT y MeteoAlarm y
los unifica en una API REST con WebSockets para actualizaciones instantáneas.

> ⚠️ **Aviso legal**: ESPAlert es un proyecto comunitario Open Source
> independiente. **No está afiliado, patrocinado ni vinculado de ninguna forma
> con el sistema ES-Alert del Gobierno de España** ni con la Dirección General
> de Protección Civil y Emergencias. ESPAlert consume exclusivamente datos
> públicos abiertos publicados por AEMET, IGN, DGT y MeteoAlarm bajo sus
> respectivas licencias. El nombre "ESPAlert" hace referencia a "España +
> Alertas" y no pretende crear confusión con ES-Alert.

<p align="center">
  <a href="../ROADMAP.md">Roadmap</a> ·
  <a href="../CHANGELOG.md">Changelog</a> ·
  <a href="../../CONTRIBUTING.md">Contribuir</a> ·
  <a href="../../SECURITY.md">Seguridad</a> ·
  <a href="../TRADEMARK_POLICY.md">Marca</a> ·
  <a href="../../.github/ISSUE_TEMPLATE/bug_report.md">Reportar bug</a> ·
  <a href="../../DOCS.md">📚 Docs Bilingüe</a> ·
  <a href="../../README.md">📖 English</a>
</p>

<p align="center">
  <em>Mapa interactivo · WebSockets en vivo · Meshtastic LoRa · RGPD/LOPDGDD</em>
</p>


---

## Tabla de contenidos

- [Arquitectura](#arquitectura)
- [Inicio rápido](#inicio-rápido)
- [Desarrollo local](#desarrollo-local)
- [Fuentes de datos](#fuentes-de-datos)
- [Variables de entorno](#variables-de-entorno)
- [Despliegue en producción](#despliegue-en-producción)
- [Roadmap](#roadmap)
- [Contribuir](#contribuir)
- [Licencia](#licencia)

---

## Arquitectura

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

| Componente       | Tecnología                                    | Ubicación          |
|------------------|-----------------------------------------------|--------------------|
| **Frontend Web** | Next.js 16, Tailwind CSS, shadcn/ui, MapLibre | `apps/web`         |
| **Backend API**  | Python 3.12, FastAPI, PostGIS, Celery, Redis  | `apps/api`         |
| **Monorepo**     | Turborepo + npm workspaces                    | Raíz               |
| **Mesh Radio**   | Meshtastic (LoRa)                             | `apps/api/connectors` |

## Inicio rápido

> **Requisitos**: [Docker](https://docs.docker.com/get-docker/) 24+ y
> [Node.js](https://nodejs.org/) 20 LTS.

```bash
# 1. Clonar el repositorio
git clone https://github.com/saasixx/ESPAlert.git
cd ESPAlert

# 2. Configurar variables de entorno
cp .env.example .env
# Ajusta AEMET_API_KEY si dispones de una (gratuita)

# 3. Levantar toda la plataforma
docker compose up --build
```

| Servicio     | URL                        |
|--------------|----------------------------|
| **Web App**  | http://localhost:3000       |
| **API REST** | http://localhost:8000       |
| **Swagger**  | http://localhost:8000/docs  |

## Desarrollo local

Si prefieres trabajar en el frontend fuera de Docker (hot-reload más rápido):

```bash
# Levantar solo infraestructura + backend
docker compose up db redis api worker beat -d

# Instalar dependencias del monorepo
npm install

# Arrancar el frontend con Turborepo
npm run dev
```

## Fuentes de datos

| Fuente         | Tipo             | Frecuencia | Formato      |
|----------------|------------------|------------|--------------|
| AEMET OpenData | Avisos meteo     | 5 min      | CAP XML      |
| IGN FDSN       | Terremotos       | 2 min      | Text/CSV     |
| DGT NAP        | Tráfico          | 5 min      | DATEX2 XML   |
| MeteoAlarm     | Avisos europeos  | 5 min      | GeoJSON/CAP  |

## Variables de entorno

Copia `.env.example` a `.env` y ajusta los valores. Las claves principales:

| Variable             | Descripción                              | Requerida |
|----------------------|------------------------------------------|-----------|
| `DATABASE_URL`       | Conexión PostgreSQL (asyncpg)            | Sí        |
| `REDIS_URL`          | Conexión Redis                           | Sí        |
| `AEMET_API_KEY`      | Clave de [AEMET OpenData][aemet] (gratis)| No*       |
| `JWT_SECRET`         | Secreto para tokens JWT (≥32 chars)      | Prod      |
| `ALLOWED_ORIGINS`    | Orígenes CORS permitidos                 | Prod      |

> \* Sin la clave de AEMET los avisos meteorológicos no estarán disponibles,
> pero el resto de fuentes (IGN, DGT, MeteoAlarm) funcionan sin autenticación.

[aemet]: https://opendata.aemet.es/centrodedescargas/inicio

## Despliegue en producción

```bash
# En el servidor:
git clone https://github.com/saasixx/ESPAlert.git /opt/espalert
cd /opt/espalert
cp .env.example .env
# ¡Edita .env con valores reales de producción!

docker compose up -d --build
```

El repositorio incluye GitHub Actions en `.github/workflows/` para CI y
despliegue automático vía SSH. Configura los secretos del repositorio:

- `SERVER_HOST` — IP o dominio del servidor.
- `SERVER_USER` — Usuario SSH.
- `SERVER_SSH_KEY` — Clave privada SSH.

## Roadmap

Consulta [ROADMAP.md](../ROADMAP.md) para ver el plan de desarrollo y las próximas
versiones. Los cambios publicados se registran en [CHANGELOG.md](../CHANGELOG.md).

| Versión | Objetivo | Estado |
|---------|----------|--------|
| **v0.1.0** | MVP público — mapa interactivo + ingesta + WebSocket | 🚧 En desarrollo |
| **v0.2.0** | Alertas personalizadas — zonas, filtros, notificaciones | 📋 Planificado |
| **v0.3.0** | Plataforma abierta — app Flutter, observabilidad, i18n | 📋 Planificado |

## Contribuir

¡Las contribuciones son bienvenidas! Lee [CONTRIBUTING.md](../../CONTRIBUTING.md)
para conocer el flujo de trabajo, las convenciones y cómo enviar un Pull Request.

**¿Nuevo en el proyecto?** Busca issues con el label
[`good first issue`](../../issues?q=label%3A%22good+first+issue%22) — tareas pequeñas y bien definidas para principiantes.

Este proyecto sigue el [Código de Conducta del Contribuidor](../../CODE_OF_CONDUCT.md).

## Seguridad

Si descubres una vulnerabilidad, **no abras un issue público**. Consulta
[SECURITY.md](../../SECURITY.md) para saber cómo reportarla de forma responsable.

## Créditos y Dependencias

ESPAlert está construido sobre software libre de calidad:

- **mapcn** — Componentes React para MapLibre GL (MIT)
- **MapLibre GL** — Motor de mapas interactivos (BSD-3-Clause)
- **FastAPI** — Framework web asincrónico (MIT)
- **PostgreSQL + PostGIS** — Base de datos geoespacial (PostgreSQL License)
- **Next.js** — Framework React con SSR (MIT)
- **Tailwind CSS** — Utilidades CSS (MIT)
- **shadcn/ui** — Componentes UI (MIT)
- **Redis** — Cache in-memory (BSD-3-Clause)
- **Celery** — Cola de tareas distribuida (BSD)

Agradecemos especialmente a [AnmolSaini16](https://github.com/AnmolSaini16/) por mapcn
y a todos los proyectos Open Source que hacen posible ESPAlert.

## Licencia

Distribuido bajo la licencia **GNU AGPL-3.0-or-later**. Ver [LICENSE](../../LICENSE).

Para proteger la identidad del proyecto, el nombre **ESPAlert**, su logotipo y
elementos de marca están sujetos a una política de marca separada.
Consulta [TRADEMARK_POLICY.md](../TRADEMARK_POLICY.md).

