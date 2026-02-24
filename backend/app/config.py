"""Application configuration — loaded from environment / .env file."""

import secrets

from pydantic_settings import BaseSettings
from pydantic import field_validator
from functools import lru_cache

# Auto-generated fallback for development only — NEVER use in production
_DEV_JWT_SECRET = secrets.token_urlsafe(48)


class Settings(BaseSettings):
    # ── App ──────────────────────────────────────────────
    APP_NAME: str = "ESPAlert"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    ENVIRONMENT: str = "development"  # development, staging, production

    # ── Database ─────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://espalert:changeme@localhost:5432/espalert"
    DATABASE_URL_SYNC: str = "postgresql+psycopg2://espalert:changeme@localhost:5432/espalert"

    # ── Redis ────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── API Keys ─────────────────────────────────────────
    AEMET_API_KEY: str = ""
    MAPBOX_TOKEN: str = ""

    # ── Firebase ─────────────────────────────────────────
    FIREBASE_CREDENTIALS_PATH: str = "firebase-credentials.json"

    # ── Polling Intervals (seconds) ──────────────────────
    AEMET_POLL_INTERVAL: int = 300       # 5 min
    IGN_POLL_INTERVAL: int = 120         # 2 min
    DGT_POLL_INTERVAL: int = 300         # 5 min
    METEOALARM_POLL_INTERVAL: int = 300  # 5 min

    # ── JWT Auth ─────────────────────────────────────────
    JWT_SECRET: str = _DEV_JWT_SECRET  # Random per-run in dev; MUST be set via .env in production
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24

    # ── Security ─────────────────────────────────────────
    ALLOWED_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:8080",
    ]
    # In production, add your actual domain:
    # ALLOWED_ORIGINS=["https://espalert.es","https://app.espalert.es"]

    RATE_LIMIT_DEFAULT: str = "100/minute"
    RATE_LIMIT_AUTH: str = "10/minute"
    RATE_LIMIT_MESH_SEND: str = "5/minute"

    # ── Meshtastic ───────────────────────────────────────
    MESHTASTIC_CONNECTION: str = "serial"
    MESHTASTIC_ADDRESS: str = "/dev/ttyUSB0"

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_origins(cls, v):
        if isinstance(v, str):
            return [o.strip() for o in v.split(",") if o.strip()]
        return v

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
