"""ESPAlert — Punto de entrada de la aplicación FastAPI."""

import logging
from contextlib import asynccontextmanager

import sqlalchemy
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from slowapi.errors import RateLimitExceeded

from app.api import auth, events, gdpr, mesh, reports, subscriptions, ws
from app.config import get_settings
from app.middleware import (
    SecurityHeadersMiddleware,
    limiter,
    rate_limit_exceeded_handler,
    validate_security_config,
)

settings = get_settings()

logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Hooks de inicio y parada de la aplicación."""
    validate_security_config()

    logger.info("🚀 %s v%s iniciando...", settings.APP_NAME, settings.APP_VERSION)
    logger.info("   Entorno: %s | Debug: %s", settings.ENVIRONMENT, settings.DEBUG)

    # Verificar conexión a la base de datos
    try:
        from app.database import engine

        async with engine.begin() as conn:
            await conn.execute(sqlalchemy.text("SELECT 1"))
        logger.info("   ✅ Base de datos conectada")
    except Exception as e:
        logger.error("   ❌ Error de conexión a la BD: %s", e)

    yield

    logger.info("👋 %s detenido.", settings.APP_NAME)


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "Sistema de alertas multi-riesgo en tiempo real para España. "
        "Agrega meteorología (AEMET), sismos (IGN), tráfico (DGT) "
        "y avisos europeos (MeteoAlarm) en una API unificada."
    ),
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# ── Pila de middleware (el último añadido se ejecuta primero) ────────────

# 1. Cabeceras de seguridad (más externo)
app.add_middleware(SecurityHeadersMiddleware)

# 2. Hosts de confianza en producción
if settings.ENVIRONMENT == "production":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.TRUSTED_HOSTS,
    )

# 3. CORS — permisivo solo en desarrollo
app.add_middleware(
    CORSMiddleware,
    allow_origins=(
        ["*"] if settings.ENVIRONMENT == "development" else settings.ALLOWED_ORIGINS
    ),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    expose_headers=["X-Request-ID"],
    max_age=3600,
)

# 4. Limitación de peticiones
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# ── Registrar routers ────────────────────────────────────────────────────
_API_PREFIX = "/api/v1"
for router_module in (events, auth, subscriptions, ws, mesh, gdpr, reports):
    app.include_router(router_module.router, prefix=_API_PREFIX)


@app.get("/")
async def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs" if settings.DEBUG else None,
        "status": "running",
        "environment": settings.ENVIRONMENT,
    }


@app.get("/health")
async def health(detailed: bool = False):
    """Comprobación de salud de la aplicación."""
    checks: dict[str, str] = {"api": "ok", "database": "unknown", "redis": "unknown"}

    try:
        from app.database import engine

        async with engine.begin() as conn:
            await conn.execute(sqlalchemy.text("SELECT 1"))
        checks["database"] = "ok"
    except Exception:
        checks["database"] = "error"

    try:
        from app.database import get_redis

        r = get_redis()
        await r.ping()
        checks["redis"] = "ok"
    except Exception:
        checks["redis"] = "error"

    status = "healthy" if all(v == "ok" for v in checks.values()) else "degraded"

    # Solo exponer detalles en modo debug
    if settings.DEBUG and detailed:
        return {"status": status, "checks": checks}
    return {"status": status}
