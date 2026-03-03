"""Esquemas Pydantic para reportes colaborativos."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.schemas.common import sanitize_html


class ReportCreate(BaseModel):
    """Creación de un reporte colaborativo ('yo lo sentí / yo lo vi')."""

    event_id: Optional[UUID] = None
    report_type: str = Field(..., max_length=50)
    intensity: str = Field(..., max_length=20)
    lat: float = Field(ge=27.0, le=44.0)
    lon: float = Field(ge=-19.0, le=5.0)
    comment: Optional[str] = Field(default=None, max_length=500)

    @field_validator("report_type")
    @classmethod
    def validate_report_type(cls, v: str) -> str:
        valid = ("rain", "wind", "shaking", "flood", "hail", "snow", "fire", "other")
        if v not in valid:
            raise ValueError(f"Report type must be one of: {valid}")
        return v

    @field_validator("intensity")
    @classmethod
    def validate_intensity(cls, v: str) -> str:
        valid = ("none", "light", "moderate", "strong", "extreme")
        if v not in valid:
            raise ValueError(f"Intensity must be one of: {valid}")
        return v

    @field_validator("comment")
    @classmethod
    def sanitize_comment(cls, v: Optional[str]) -> Optional[str]:
        if v:
            v = sanitize_html(v)
        return v


class ReportOut(BaseModel):
    id: UUID
    report_type: str
    intensity: str
    lat: float
    lon: float
    comment: Optional[str]
    event_id: Optional[UUID] = None
    created_at: datetime

    model_config = {"from_attributes": True}
