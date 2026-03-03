"""Esquemas Pydantic para zonas y filtros de suscripción."""

import json as _json
import re
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.schemas.common import sanitize_html


class ZoneCreate(BaseModel):
    label: str = Field(max_length=100, min_length=1)
    geojson: dict

    @field_validator("label")
    @classmethod
    def sanitize_label(cls, v: str) -> str:
        return sanitize_html(v)

    @field_validator("geojson")
    @classmethod
    def validate_geojson(cls, v: dict) -> dict:
        """Validación básica de GeoJSON con límite de tamaño."""
        serialized = _json.dumps(v)
        if len(serialized) > 100_000:
            raise ValueError("GeoJSON payload too large (max 100 KB)")
        if "type" not in v:
            raise ValueError("GeoJSON must have 'type' field")
        valid_types = ("Point", "Polygon", "MultiPolygon", "LineString", "GeometryCollection")
        if v["type"] not in valid_types:
            raise ValueError(f"GeoJSON type must be one of: {valid_types}")
        if "coordinates" not in v and v["type"] != "GeometryCollection":
            raise ValueError("GeoJSON must have 'coordinates' field")

        def _max_depth(obj: object, depth: int = 0) -> int:
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


class FilterCreate(BaseModel):
    event_types: Optional[list[str]] = Field(default=None, max_length=10)
    min_severity: str = "yellow"

    @field_validator("min_severity")
    @classmethod
    def validate_min_severity(cls, v: str) -> str:
        if v not in ("green", "yellow", "orange", "red"):
            raise ValueError("Severity must be: green, yellow, orange, red")
        return v

    @field_validator("event_types")
    @classmethod
    def validate_event_types(cls, v: Optional[list[str]]) -> Optional[list[str]]:
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
