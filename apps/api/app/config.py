"""Application configuration — loaded from environment variables / .env."""

import secrets
from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings

# Auto-generated secret for development; NEVER use in production
_DEV_JWT_SECRET = secrets.token_urlsafe(48)


class Settings(BaseSettings):
    """Central ESPAlert configuration.

    All values can be overridden via environment variables
    or a ``.env`` file at the project root.
    """

    # ── Application ──────────────────────────────────────
    APP_NAME: str = "ESPAlert"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True
    ENVIRONMENT: str = "development"  # development | staging | production

    # ── Database ─────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://espalert:changeme@localhost:5432/espalert"
    DATABASE_URL_SYNC: str = "postgresql+psycopg2://espalert:changeme@localhost:5432/espalert"

    # ── Redis ────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── External keys ────────────────────────────────────
    AEMET_API_KEY: str = ""

    # ── Firebase ─────────────────────────────────────────
    FIREBASE_CREDENTIALS_PATH: str = "firebase-credentials.json"

    # ── Polling intervals (seconds) ──────────────────────
    AEMET_POLL_INTERVAL: int = 300  # 5 min
    IGN_POLL_INTERVAL: int = 120  # 2 min
    DGT_POLL_INTERVAL: int = 300  # 5 min
    METEOALARM_POLL_INTERVAL: int = 300  # 5 min

    # ── JWT Authentication ───────────────────────────────
    JWT_SECRET: str = _DEV_JWT_SECRET  # Random per run in dev
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24

    # ── Security ─────────────────────────────────────────
    ALLOWED_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:8080",
        "https://esp-alert-web.vercel.app",
    ]

    TRUSTED_HOSTS: list[str] = [
        "localhost",
        "127.0.0.1",
    ]

    RATE_LIMIT_DEFAULT: str = "100/minute"
    RATE_LIMIT_AUTH: str = "10/minute"
    RATE_LIMIT_MESH_SEND: str = "5/minute"

    # ── Meshtastic ───────────────────────────────────────
    MESHTASTIC_CONNECTION: str = "serial"
    MESHTASTIC_ADDRESS: str = "/dev/ttyUSB0"

    @field_validator("ALLOWED_ORIGINS", "TRUSTED_HOSTS", mode="before")
    @classmethod
    def parse_origins(cls, v: str | list[str]) -> list[str]:
        """Allow passing origins as a comma-separated string."""
        if isinstance(v, str):
            return [o.strip() for o in v.split(",") if o.strip()]
        return v

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()
