"""Pydantic schemas for API request/response serialization (hardened)."""

import re
from datetime import datetime, time
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator


# ── Events ───────────────────────────────────────────────────────────────────

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

    model_config = {"from_attributes": True}


class EventListParams(BaseModel):
    """Query parameters for filtering events."""
    event_type: Optional[str] = None
    severity: Optional[str] = None
    source: Optional[str] = None
    active_only: bool = True
    lat: Optional[float] = Field(default=None, ge=27.0, le=44.0)   # Spain bounds
    lon: Optional[float] = Field(default=None, ge=-19.0, le=5.0)
    radius_km: Optional[float] = Field(default=50.0, ge=1.0, le=500.0)
    limit: int = Field(default=50, le=200, ge=1)
    offset: int = Field(default=0, ge=0)

    @field_validator("severity")
    @classmethod
    def validate_severity(cls, v):
        if v and v not in ("green", "yellow", "orange", "red"):
            raise ValueError("Severity must be: green, yellow, orange, red")
        return v


# ── Users ────────────────────────────────────────────────────────────────────

# Password: min 8 chars, at least 1 uppercase, 1 lowercase, 1 digit
PASSWORD_REGEX = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,72}$")


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    display_name: Optional[str] = Field(default=None, max_length=50)

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v):
        if not PASSWORD_REGEX.match(v):
            raise ValueError(
                "La contraseña debe tener al menos 8 caracteres, "
                "una mayúscula, una minúscula y un número."
            )
        return v

    @field_validator("display_name")
    @classmethod
    def sanitize_display_name(cls, v):
        if v:
            # Strip HTML tags
            v = re.sub(r"<[^>]+>", "", v).strip()
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(max_length=72)


class UserOut(BaseModel):
    id: UUID
    email: str
    display_name: Optional[str]
    quiet_start: Optional[time]
    quiet_end: Optional[time]
    predictive_alerts: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ── Zones ────────────────────────────────────────────────────────────────────

class ZoneCreate(BaseModel):
    label: str = Field(max_length=100, min_length=1)
    geojson: dict  # GeoJSON geometry

    @field_validator("label")
    @classmethod
    def sanitize_label(cls, v):
        return re.sub(r"<[^>]+>", "", v).strip()

    @field_validator("geojson")
    @classmethod
    def validate_geojson(cls, v):
        """Basic GeoJSON validation with size limit."""
        import json as _json
        serialized = _json.dumps(v)
        if len(serialized) > 100_000:  # 100 KB max
            raise ValueError("GeoJSON payload too large (max 100 KB)")
        if "type" not in v:
            raise ValueError("GeoJSON must have 'type' field")
        valid_types = ("Point", "Polygon", "MultiPolygon", "LineString", "GeometryCollection")
        if v["type"] not in valid_types:
            raise ValueError(f"GeoJSON type must be one of: {valid_types}")
        if "coordinates" not in v and v["type"] != "GeometryCollection":
            raise ValueError("GeoJSON must have 'coordinates' field")
        # Limit coordinate nesting depth
        def _max_depth(obj, depth=0):
            if isinstance(obj, dict):
                return max((_max_depth(v2, depth + 1) for v2 in obj.values()), default=depth)
            elif isinstance(obj, list):
                return max((_max_depth(i, depth + 1) for i in obj), default=depth)
            return depth
        if _max_depth(v) > 15:
            raise ValueError("GeoJSON nesting too deep")
        return v


class ZoneOut(BaseModel):
    id: UUID
    label: str
    geojson: Optional[dict] = None

    model_config = {"from_attributes": True}


# ── Filters ──────────────────────────────────────────────────────────────────

class FilterCreate(BaseModel):
    event_types: Optional[list[str]] = Field(default=None, max_length=10)
    min_severity: str = "yellow"

    @field_validator("min_severity")
    @classmethod
    def validate_min_severity(cls, v):
        if v not in ("green", "yellow", "orange", "red"):
            raise ValueError("Severity must be: green, yellow, orange, red")
        return v

    @field_validator("event_types")
    @classmethod
    def validate_event_types(cls, v):
        if v:
            valid = {"meteo", "seismic", "traffic", "maritime", "fire", "flood", "heatwave", "tsunami"}
            for t in v:
                if t not in valid:
                    raise ValueError(f"Unknown event type: {t}. Valid: {valid}")
        return v


class FilterOut(BaseModel):
    id: UUID
    event_types: Optional[list[str]]
    min_severity: str

    model_config = {"from_attributes": True}


# ── Collaborative Reports ────────────────────────────────────────────────────

class ReportCreate(BaseModel):
    event_id: Optional[UUID] = None
    report_type: str
    intensity: str
    lat: float = Field(ge=27.0, le=44.0)    # Spain bounds
    lon: float = Field(ge=-19.0, le=5.0)
    comment: Optional[str] = Field(default=None, max_length=500)

    @field_validator("report_type")
    @classmethod
    def validate_report_type(cls, v):
        valid = ("rain", "wind", "shaking", "flood", "hail", "snow", "fire", "other")
        if v not in valid:
            raise ValueError(f"Report type must be one of: {valid}")
        return v

    @field_validator("intensity")
    @classmethod
    def validate_intensity(cls, v):
        valid = ("none", "light", "moderate", "strong", "extreme")
        if v not in valid:
            raise ValueError(f"Intensity must be one of: {valid}")
        return v

    @field_validator("comment")
    @classmethod
    def sanitize_comment(cls, v):
        if v:
            v = re.sub(r"<[^>]+>", "", v).strip()
        return v


class ReportOut(BaseModel):
    id: UUID
    report_type: str
    intensity: str
    lat: float
    lon: float
    comment: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Settings Update ──────────────────────────────────────────────────────────

class UserSettingsUpdate(BaseModel):
    quiet_start: Optional[time] = None
    quiet_end: Optional[time] = None
    predictive_alerts: Optional[bool] = None
    fcm_token: Optional[str] = Field(default=None, max_length=256)
