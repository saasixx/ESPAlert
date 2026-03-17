"""ESPAlert — FastAPI application entry point."""

import logging
import os
from contextlib import asynccontextmanager

import sqlalchemy
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from slowapi.errors import RateLimitExceeded

from app.api import auth, events, gdpr, mesh, reports, subscriptions, ws
from app.config import get_settings
from app.logging_config import setup_logging
from app.middleware import (
    SecurityHeadersMiddleware,
    limiter,
    rate_limit_exceeded_handler,
    validate_security_config,
)

settings = get_settings()
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Application startup and shutdown hooks."""
    validate_security_config()

    if not os.environ.get("JWT_SECRET"):
        logger.warning("JWT_SECRET not set — using ephemeral dev secret. All tokens will be invalid after restart.")

    logger.info("🚀 %s v%s starting...", settings.APP_NAME, settings.APP_VERSION)
    logger.info("   Environment: %s | Debug: %s", settings.ENVIRONMENT, settings.DEBUG)

    # Verify database connection
    try:
        from app.database import engine

        async with engine.begin() as conn:
            await conn.execute(sqlalchemy.text("SELECT 1"))
        logger.info("   ✅ Database connected")
    except Exception as e:
        logger.error("   ❌ Database connection error: %s", e)

    yield

    logger.info("👋 %s stopped.", settings.APP_NAME)


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

# ── Middleware stack (last added runs first) ────────────────────────────

# 1. Security headers (outermost)
app.add_middleware(SecurityHeadersMiddleware)

# 2. Trusted hosts in production
if settings.ENVIRONMENT == "production":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.TRUSTED_HOSTS,
    )

# 3. CORS — permissive in development only
app.add_middleware(
    CORSMiddleware,
    allow_origins=(["*"] if settings.ENVIRONMENT == "development" else settings.ALLOWED_ORIGINS),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    expose_headers=["X-Request-ID"],
    max_age=3600,
)

# 4. Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# ── Register routers ─────────────────────────────────────────────────────
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
    """Application health check with component latency.

    Probes the database and Redis connections and measures their response
    latency. Returns an overall status of ``healthy`` or ``degraded``.

    In ``DEBUG`` mode, or when ``detailed=True``, the response is expanded to
    include per-component check results (with latency), the application version,
    the runtime environment, and optional ingest statistics for the last hour.

    Args:
        detailed: If ``True``, include full per-component checks, latency
            figures, version, environment, and ingest statistics in the
            response body.

    Returns:
        Dict containing ``status`` (``"healthy"`` or ``"degraded"``), and
        optionally ``checks``, ``version``, ``environment``, and
        ``ingest_last_hour`` when ``detailed=True`` or running in DEBUG mode.
    """
    import time as _time

    checks: dict[str, dict] = {
        "api": {"status": "ok"},
        "database": {"status": "unknown"},
        "redis": {"status": "unknown"},
    }

    # --- Database ---
    try:
        from app.database import engine

        start = _time.monotonic()
        async with engine.begin() as conn:
            await conn.execute(sqlalchemy.text("SELECT 1"))
        latency_ms = round((_time.monotonic() - start) * 1000, 1)
        checks["database"] = {"status": "ok", "latency_ms": latency_ms}
    except Exception as e:
        checks["database"] = {"status": "error", "error": str(e)[:120]}

    # --- Redis ---
    try:
        from app.database import get_redis

        r = get_redis()
        start = _time.monotonic()
        await r.ping()
        latency_ms = round((_time.monotonic() - start) * 1000, 1)
        checks["redis"] = {"status": "ok", "latency_ms": latency_ms}
    except Exception as e:
        checks["redis"] = {"status": "error", "error": str(e)[:120]}

    # --- Ingest statistics (if data exists in Redis) ---
    ingest_stats = None
    if detailed:
        try:
            import json

            r = get_redis()
            raw = await r.get("espalert:stats:ingest_1h")
            if raw:
                ingest_stats = json.loads(raw)
        except Exception:
            pass

    all_ok = all(c["status"] == "ok" for c in checks.values())
    status = "healthy" if all_ok else "degraded"

    result: dict = {"status": status}

    if settings.DEBUG or detailed:
        result["checks"] = checks
        if ingest_stats:
            result["ingest_last_hour"] = ingest_stats
        result["version"] = settings.APP_VERSION
        result["environment"] = settings.ENVIRONMENT

    return result
