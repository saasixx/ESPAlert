# ESPAlert 🛡️

**Sistema de alertas multi-riesgo en tiempo real para España**

*ESPAlert* es una plataforma Open Source diseñada para proporcionar alertas tempranas de meteorología, sismos, tráfico y avisos de protección civil en un único mapa interactivo. 

> **Aviso de Migración:** El proyecto ha sido reescrito desde Flutter a **Next.js + MapLibre GL** para abrirlo a la comunidad web Open Source. La versión Flutter original reside en `app_flutter_archive/`.

## 📦 Arquitectura (Monorepo)

| Componente | Tecnología | Ubicación |
|---|---|---|
| **Frontend Web** | Next.js 15, Tailwind, shadcn/ui, MapLibre GL | `/apps/web` |
| **Backend API** | Python 3.12, FastAPI, PostGIS, Celery, Redis | `/apps/api` |
| **Monorepo** | Turborepo | Raíz |
| **Mesh Radio** | Meshtastic (LoRa) | `/apps/api/connectors` |

## 🗂️ Estructura del repositorio

```text
ESPAlert/
├── apps/
│   ├── api/                    # FastAPI + Celery + PostGIS
│   └── web/                    # Next.js App Router (Frontend)
├── app_flutter_archive/        # Versión móvil antigua (Deprecated)
├── docker-compose.yml          # Full stack (¡la forma recomendada!)
├── package.json                # Turborepo workspaces
└── turbo.json
```

## 🚀 Instalación y Despliegue Rápido (Docker)

La forma más rápida de levantar toda la plataforma (Base de datos espacial, Redis, Backend FastAPI, Workers y el Frontend Web):

```bash
# 1. Clona el repositorio
git clone https://github.com/tu-usuario/ESPAlert.git
cd ESPAlert

# 2. Configura las variables de entorno del backend
cp apps/api/.env.example apps/api/.env
# (Edita .env si tienes API Keys reales de AEMET, si no, funcionará con datos públicos)

# 3. Levanta el stack completo
npm run dev:docker
```

La aplicación estará disponible en:
- **Web App**: http://localhost:3000
- **API REST**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## 🛠️ Desarrollo Local (Sin Docker para el Frontend)

Si prefieres desarrollar el frontend fuera de Docker (para recargas más rápidas):

```bash
# 1. Levanta solo la base de datos y backend con Docker
docker compose up db redis api worker beat -d

# 2. Instala dependencias del monorepo
npm install

# 3. Levanta el frontend con Turborepo
npm run dev
```

## 📡 Fuentes de datos

| Fuente | Tipo | Frecuencia | Formato |
|---|---|---|---|
| AEMET OpenData | Avisos meteo | 5 min | CAP XML |
| IGN FDSN | Terremotos | 2 min | Text/CSV |
| DGT NAP | Tráfico | 5 min | DATEX2 XML |
| MeteoAlarm EDR | Avisos europeos | 5 min | GeoJSON |

## 🔑 Claves necesarias

1. **AEMET**: [Obtener API key](https://opendata.aemet.es/centrodedescargas/inicio) (gratuita)
2. **Firebase**: Crear proyecto en [console.firebase.google.com](https://console.firebase.google.com)
3. **JWT_SECRET**: Generar string aleatorio para producción
