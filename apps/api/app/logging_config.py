"""Configuración de logging estructurado para ESPAlert.

En producción, emite JSON. En desarrollo, emite texto coloreado legible.
"""

import logging
import sys
from typing import Optional

from app.config import get_settings


def setup_logging(level: Optional[str] = None) -> None:
    """Configura logging para toda la aplicación."""
    settings = get_settings()
    log_level = level or ("DEBUG" if settings.DEBUG else "INFO")
    is_production = settings.ENVIRONMENT == "production"

    root = logging.getLogger()
    root.setLevel(log_level)

    # Eliminar handlers previos
    for handler in root.handlers[:]:
        root.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)

    if is_production:
        handler.setFormatter(_JsonFormatter())
    else:
        handler.setFormatter(_ColorFormatter())

    root.addHandler(handler)

    # Reducir ruido de librerías externas
    for noisy in ("uvicorn.access", "httpx", "httpcore", "asyncio", "sqlalchemy.engine"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    logging.getLogger("uvicorn.error").setLevel(logging.INFO)


class _JsonFormatter(logging.Formatter):
    """Formateador JSON para producción — compatible con Loki/ELK/CloudWatch."""

    def format(self, record: logging.LogRecord) -> str:
        import json
        from datetime import datetime, timezone

        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if record.exc_info and record.exc_info[1]:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Incluir campos extra si están en el record
        for key in ("request_id", "user_id", "source", "event_id", "duration_ms"):
            val = getattr(record, key, None)
            if val is not None:
                log_entry[key] = val

        return json.dumps(log_entry, ensure_ascii=False)


class _ColorFormatter(logging.Formatter):
    """Formateador con colores ANSI para desarrollo."""

    COLORS = {
        "DEBUG": "\033[36m",    # Cyan
        "INFO": "\033[32m",     # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",    # Red
        "CRITICAL": "\033[41m", # Red background
    }
    RESET = "\033[0m"
    GREY = "\033[90m"

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, "")
        level = f"{color}{record.levelname:8s}{self.RESET}"
        name = f"{self.GREY}{record.name}{self.RESET}"

        msg = f"{level} {name}: {record.getMessage()}"

        if record.exc_info and record.exc_info[1]:
            msg += f"\n{self.formatException(record.exc_info)}"

        return msg
