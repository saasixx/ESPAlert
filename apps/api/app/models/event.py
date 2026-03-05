"""Unified Event model — all data sources are normalized here."""

import enum
import uuid

from geoalchemy2 import Geometry
from sqlalchemy import (
    Column, String, Text, DateTime, Enum as SAEnum,
    func, Index,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.database import Base


# ── Enumerations ─────────────────────────────────────────────────────────────


class EventSource(str, enum.Enum):
    AEMET = "aemet"
    IGN = "ign"
    DGT = "dgt"
    METEOALARM = "meteoalarm"
    ESALERT = "esalert"


class EventType(str, enum.Enum):
    """Supported event types."""

    # Meteorological
    WIND = "wind"
    RAIN = "rain"
    STORM = "storm"
    SNOW = "snow"
    ICE = "ice"
    FOG = "fog"
    HEAT = "heat"
    COLD = "cold"
    UV = "uv"
    FIRE_RISK = "fire_risk"
    # Coastal / Maritime
    COASTAL = "coastal"
    WAVE = "wave"
    TIDE = "tide"
    # Seismic
    EARTHQUAKE = "earthquake"
    TSUNAMI = "tsunami"
    # Traffic
    TRAFFIC_ACCIDENT = "traffic_accident"
    TRAFFIC_CLOSURE = "traffic_closure"
    TRAFFIC_WORKS = "traffic_works"
    TRAFFIC_JAM = "traffic_jam"
    # Civil protection
    CIVIL_PROTECTION = "civil_protection"
    # Generic / other
    OTHER = "other"


class Severity(str, enum.Enum):
    """Event severity level."""

    GREEN = "green"      # No significant risk
    YELLOW = "yellow"    # Low risk — be aware
    ORANGE = "orange"    # Moderate risk — be prepared
    RED = "red"          # High risk — take action


# ── Model ────────────────────────────────────────────────────────────────────


class Event(Base):
    """Normalized alert event stored in PostgreSQL/PostGIS."""

    __tablename__ = "events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source = Column(SAEnum(EventSource, name="event_source"), nullable=False, index=True)
    source_id = Column(String(255), unique=True, nullable=False)  # Deduplication key

    event_type = Column(SAEnum(EventType, name="event_type"), nullable=False, index=True)
    severity = Column(SAEnum(Severity, name="severity"), nullable=False, index=True)

    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    instructions = Column(Text, nullable=True)  # Safety recommendations

    # PostGIS geometry — stores polygons, multipolygons or points
    area = Column(Geometry("GEOMETRY", srid=4326), nullable=True)
    area_name = Column(String(500), nullable=True)

    # Time bounds
    effective = Column(DateTime(timezone=True), nullable=True)  # Event start
    expires = Column(DateTime(timezone=True), nullable=True)    # Event end

    # Metadata
    source_url = Column(String(1000), nullable=True)
    raw_data = Column(JSONB, nullable=True)

    # Earthquake-specific (null for other types)
    magnitude = Column(String(10), nullable=True)
    depth_km = Column(String(10), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        Index("idx_events_active", "effective", "expires"),
        Index("idx_events_area", "area", postgresql_using="gist"),
    )

    def __repr__(self):
        return f"<Event {self.event_type.value} [{self.severity.value}] — {self.title[:50]}>"
