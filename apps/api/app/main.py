"""ESPAlert — FastAPI application entry point (production-hardened)."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.config import get_settings
from app.api import events, auth, subscriptions, ws, mesh
from app.api import gdpr, reports
from app.middleware import (
    SecurityHeadersMiddleware,
    limiter,
    rate_limit_exceeded_handler,
    validate_security_config,
)

settings = get_settings()

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup & shutdown hooks."""
    # Security validation
    validate_security_config()

    logger.info(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION} starting...")
    logger.info(f"   Environment: {settings.ENVIRONMENT}")
    logger.info(f"   Debug: {settings.DEBUG}")
    logger.info(f"   Allowed origins: {settings.ALLOWED_ORIGINS}")

    # Verify DB connection
    try:
        from app.database import engine
        async with engine.begin() as conn:
            await conn.execute(
                __import__("sqlalchemy").text("SELECT 1")
            )
        logger.info("   ✅ Database connected")
    except Exception as e:
        logger.error(f"   ❌ Database connection failed: {e}")

    yield

    logger.info(f"👋 {settings.APP_NAME} shutting down...")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "Multi-hazard real-time alert system for Spain. "
        "Aggregates weather (AEMET), earthquakes (IGN), traffic (DGT), "
        "and European warnings (MeteoAlarm) into a unified API."
    ),
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,     # Disable in production
    redoc_url="/redoc" if settings.DEBUG else None,
)

# ── Middleware stack (order matters: last added = first executed) ─────────

# 1. Security headers (outermost)
app.add_middleware(SecurityHeadersMiddleware)

# 2. Trusted hosts in production
if settings.ENVIRONMENT == "production":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.TRUSTED_HOSTS,
    )

# 3. CORS — restrictive in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS if settings.ENVIRONMENT != "development" else ["*"],
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
app.include_router(events.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")
app.include_router(subscriptions.router, prefix="/api/v1")
app.include_router(ws.router, prefix="/api/v1")
app.include_router(mesh.router, prefix="/api/v1")
app.include_router(gdpr.router, prefix="/api/v1")
app.include_router(reports.router, prefix="/api/v1")


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
    """Health check endpoint. Detailed checks only in debug mode."""
    checks = {"api": "ok", "database": "unknown", "redis": "unknown"}

    try:
        from app.database import engine
        async with engine.begin() as conn:
            await conn.execute(__import__("sqlalchemy").text("SELECT 1"))
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

    # Only expose component details in debug mode
    if settings.DEBUG and detailed:
        return {"status": status, "checks": checks}
    return {"status": status}
