# ESPAlert 🛡️

**Sistema de alertas multi-riesgo en tiempo real para España**

Inspirado en [Yurekuru](https://play.google.com/store/apps/details?id=jp.co.rcsc.yurekuru.android): suscripción por zonas, mapa vivo, lista de eventos y avisos altamente configurables — pero para meteorología, sismos, tráfico y protección civil.

## 📦 Stack

| Componente | Tecnología |
|---|---|
| Backend API | Python 3.12 + FastAPI |
| Base de datos | PostgreSQL 16 + PostGIS |
| Caché/Cola | Redis 7 |
| Workers | Celery (Beat + Worker) |
| Push | Firebase Cloud Messaging |
| App móvil | Flutter 3.x (Android + iOS) |
| Mapas | flutter_map + CartoDB dark tiles |
| Mesh Radio | Meshtastic (LoRa) — chat sin cobertura |

## 🗂️ Estructura

```
ESPAlert/
├── backend/                    # FastAPI + Celery
│   ├── app/
│   │   ├── main.py             # Entry point
│   │   ├── config.py           # Settings
│   │   ├── database.py         # SQLAlchemy async
│   │   ├── schemas.py          # Pydantic schemas
│   │   ├── models/             # SQLAlchemy + GeoAlchemy2
│   │   ├── connectors/         # AEMET, IGN, DGT, MeteoAlarm
│   │   ├── services/           # Normalizer, GeoEngine, Notifications
│   │   ├── tasks/              # Celery periodic ingestion
│   │   └── api/                # REST + WebSocket endpoints
│   ├── alembic/                # DB migrations
│   ├── docker-compose.yml      # Full stack
│   ├── Dockerfile
│   └── requirements.txt
│
└── app/                        # Flutter mobile app
    ├── lib/
    │   ├── main.dart
    │   ├── config/theme.dart
    │   ├── models/event.dart
    │   ├── services/api_service.dart
    │   ├── providers/
    │   ├── screens/            # Map, Timeline, Mesh, Detail, History, Education, Settings
    │   └── widgets/            # EventCard, SeverityBadge, LayerToggle, Countdown
    └── pubspec.yaml
```

## 🚀 Quick Start

### Backend

```bash
cd backend
cp .env.example .env
# Edit .env with your AEMET API key

docker compose up --build
```

Esto levanta: PostgreSQL+PostGIS, Redis, API (puerto 8000), Worker, Beat.

- API docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health

### Meshtastic Gateway (opcional)

Si tienes un dispositivo Meshtastic conectado por USB:

```bash
docker compose --profile mesh up --build
```

También puedes ejecutar el gateway directamente:

```bash
python -m app.connectors.meshtastic_gw --type serial --address /dev/ttyUSB0
# o por TCP si usas un nodo remoto:
python -m app.connectors.meshtastic_gw --type tcp --address 192.168.1.50
```

### Flutter App

```bash
cd app
flutter pub get
flutter run
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
