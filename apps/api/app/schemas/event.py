"""Esquemas Pydantic para eventos de alerta."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class EventOut(BaseModel):
    """Representación pública de un evento de alerta."""

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

    model_config = {"from_attributes": True}


class EventListParams(BaseModel):
    """Parámetros de consulta para filtrar eventos."""

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
