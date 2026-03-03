"""Paquete de esquemas Pydantic — re-exporta todo para compatibilidad con imports existentes."""

from app.schemas.event import EventOut, EventListParams
from app.schemas.auth import (
    UserCreate,
    UserLogin,
    UserOut,
    TokenOut,
    UserSettingsUpdate,
)
from app.schemas.subscription import (
    ZoneCreate,
    ZoneOut,
    FilterCreate,
    FilterOut,
)
from app.schemas.report import ReportCreate, ReportOut

__all__ = [
    "EventOut",
    "EventListParams",
    "UserCreate",
    "UserLogin",
    "UserOut",
    "TokenOut",
    "UserSettingsUpdate",
    "ZoneCreate",
    "ZoneOut",
    "FilterCreate",
    "FilterOut",
    "ReportCreate",
    "ReportOut",
]
