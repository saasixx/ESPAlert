"""Configuración de la aplicación — cargada desde variables de entorno / .env."""

import secrets
from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings

# Secreto auto-generado para desarrollo; NUNCA usar en producción
_DEV_JWT_SECRET = secrets.token_urlsafe(48)


class Settings(BaseSettings):
    """Configuración central de ESPAlert.

    Todos los valores pueden sobrescribirse con variables de entorno
    o con un fichero ``.env`` en la raíz del proyecto.
    """

    # ── Aplicación ───────────────────────────────────────
    APP_NAME: str = "ESPAlert"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True
    ENVIRONMENT: str = "development"  # development | staging | production

    # ── Base de datos ────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://espalert:changeme@localhost:5432/espalert"
    DATABASE_URL_SYNC: str = "postgresql+psycopg2://espalert:changeme@localhost:5432/espalert"

    # ── Redis ────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── Claves externas ──────────────────────────────────
    AEMET_API_KEY: str = ""

    # ── Firebase ─────────────────────────────────────────
    FIREBASE_CREDENTIALS_PATH: str = "firebase-credentials.json"

    # ── Intervalos de sondeo (segundos) ──────────────────
    AEMET_POLL_INTERVAL: int = 300       # 5 min
    IGN_POLL_INTERVAL: int = 120         # 2 min
    DGT_POLL_INTERVAL: int = 300         # 5 min
    METEOALARM_POLL_INTERVAL: int = 300  # 5 min

    # ── Autenticación JWT ────────────────────────────────
    JWT_SECRET: str = _DEV_JWT_SECRET  # Aleatorio por ejecución en dev
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24

    # ── Seguridad ────────────────────────────────────────
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
        """Permite pasar orígenes como cadena separada por comas."""
        if isinstance(v, str):
            return [o.strip() for o in v.split(",") if o.strip()]
        return v

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    """Singleton cacheado de la configuración."""
    return Settings()
