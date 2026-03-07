"""Pydantic schemas for alert events."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, computed_field, field_validator

# Mapping from event_type value to frontend icon category
_SEISMIC_TYPES = {"earthquake", "tsunami"}
_TRAFFIC_PREFIX = "traffic"
_MARITIME_TYPES = {"coastal", "wave", "tide"}


def _derive_icon_key(event_type: str) -> str:
    """Derive the frontend icon category from event_type."""
    if event_type in _SEISMIC_TYPES:
        return "seismic"
    if event_type.startswith(_TRAFFIC_PREFIX):
        return "traffic"
    if event_type in _MARITIME_TYPES:
        return "maritime"
    return "meteo"


class EventOut(BaseModel):
    """Public representation of an alert event."""

    id: UUID
    source: str
    source_id: str
    event_type: str
    severity: str
    title: str
    description: Optional[str] = None
    instructions: Optional[str] = None
    area_name: Optional[str] = None
    area_geojson: Optional[dict] = None
    effective: Optional[datetime] = None
    expires: Optional[datetime] = None
    source_url: Optional[str] = None
    magnitude: Optional[str] = None
    depth_km: Optional[str] = None
    created_at: datetime

    @computed_field  # type: ignore[misc]
    @property
    def icon_key(self) -> str:
        """Frontend icon category derived from event_type (no DB column needed)."""
        return _derive_icon_key(self.event_type)

    model_config = {"from_attributes": True}


class EventListParams(BaseModel):
    """Query parameters for filtering events."""

    event_type: Optional[str] = None
    severity: Optional[str] = None
    source: Optional[str] = None
    active_only: bool = True
    lat: Optional[float] = Field(default=None, ge=27.0, le=44.0)
    lon: Optional[float] = Field(default=None, ge=-19.0, le=5.0)
    radius_km: Optional[float] = Field(default=50.0, ge=1.0, le=500.0)
    limit: int = Field(default=50, le=200, ge=1)
    offset: int = Field(default=0, ge=0)

    @field_validator("severity")
    @classmethod
    def validate_severity(cls, v: Optional[str]) -> Optional[str]:
        if v and v not in ("green", "yellow", "orange", "red"):
            raise ValueError("Severity must be: green, yellow, orange, red")
        return v
