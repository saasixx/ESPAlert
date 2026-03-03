"""Modelos SQLAlchemy — importar todos para que Alembic los detecte."""

from app.models.event import Event, EventSource, EventType, Severity  # noqa: F401
from app.models.user import User, UserZone, UserFilter  # noqa: F401
from app.models.report import CollaborativeReport  # noqa: F401
