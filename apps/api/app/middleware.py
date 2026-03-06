"""Security middleware — headers, rate limiting, request tracking."""

import time
import uuid
import logging
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


# ── Rate Limiter ─────────────────────────────────────────────────────────────

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100/minute"],
    storage_uri=settings.REDIS_URL,
)


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    return JSONResponse(
        status_code=429,
        content={
            "error": "rate_limit_exceeded",
            "detail": "Demasiadas peticiones. Inténtalo de nuevo más tarde.",
            "retry_after": exc.detail,
        },
    )


# ── Security headers middleware ───────────────────────────────────────


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate request ID for traceability
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        start = time.time()
        response = await call_next(request)
        duration = time.time() - start

        # Security headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=(self), payment=(), usb=(), bluetooth=(self)"
        )

        # HSTS in production only
        if settings.ENVIRONMENT == "production":
            response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"

        # Content security policy
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https://*.basemaps.cartocdn.com; "
            "connect-src 'self' wss: ws:; "
            "frame-ancestors 'none'"
        )

        # Response time (debug only)
        if settings.DEBUG:
            response.headers["X-Response-Time"] = f"{duration:.3f}s"

        # Access log
        logger.info(
            "[%s] %s %s → %s (%.3fs)",
            request_id,
            request.method,
            request.url.path,
            response.status_code,
            duration,
        )

        return response


# ── Security validation at startup ──────────────────────────────────


def validate_security_config() -> None:
    """Runs at startup to detect insecure configurations."""
    warnings: list[str] = []
    errors: list[str] = []

    if len(settings.JWT_SECRET) < 32:
        if settings.ENVIRONMENT == "production":
            errors.append("JWT_SECRET must be at least 32 characters in production.")
        else:
            warnings.append("JWT_SECRET is too short — set a strong value in .env")

    if settings.DEBUG and settings.ENVIRONMENT == "production":
        errors.append("DEBUG must be False in production.")

    if not settings.AEMET_API_KEY:
        warnings.append("AEMET_API_KEY is not set — weather data will not be available")

    for w in warnings:
        logger.warning("⚠️  Security: %s", w)
    for e in errors:
        logger.error("🔴 Security: %s", e)

    if errors:
        raise RuntimeError(
            "Security configuration errors detected. Fix the errors above before starting in production."
        )
