"""Modelo unificado de Evento — todas las fuentes de datos se normalizan aquí."""

import enum
import uuid

from geoalchemy2 import Geometry
from sqlalchemy import (
    Column, String, Text, DateTime, Enum as SAEnum,
    func, Index,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.database import Base


# ── Enumeraciones ────────────────────────────────────────────────────────────


class EventSource(str, enum.Enum):
    AEMET = "aemet"
    IGN = "ign"
    DGT = "dgt"
    METEOALARM = "meteoalarm"
    ESALERT = "esalert"


class EventType(str, enum.Enum):
    """Tipos de evento soportados."""

    # Meteorológico
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
    # Costero / Marítimo
    COASTAL = "coastal"
    WAVE = "wave"
    TIDE = "tide"
    # Sísmico
    EARTHQUAKE = "earthquake"
    TSUNAMI = "tsunami"
    # Tráfico
    TRAFFIC_ACCIDENT = "traffic_accident"
    TRAFFIC_CLOSURE = "traffic_closure"
    TRAFFIC_WORKS = "traffic_works"
    TRAFFIC_JAM = "traffic_jam"
    # Protección civil
    CIVIL_PROTECTION = "civil_protection"
    # Genérico / otros
    OTHER = "other"


class Severity(str, enum.Enum):
    """Nivel de severidad del evento."""

    GREEN = "green"      # Sin riesgo significativo
    YELLOW = "yellow"    # Riesgo bajo — estar atento
    ORANGE = "orange"    # Riesgo moderado — estar preparado
    RED = "red"          # Riesgo alto — actuar


# ── Modelo ───────────────────────────────────────────────────────────────────


class Event(Base):
    """Evento de alerta normalizado almacenado en PostgreSQL/PostGIS."""

    __tablename__ = "events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source = Column(SAEnum(EventSource, name="event_source"), nullable=False, index=True)
    source_id = Column(String(255), unique=True, nullable=False)  # Clave de deduplicación

    event_type = Column(SAEnum(EventType, name="event_type"), nullable=False, index=True)
    severity = Column(SAEnum(Severity, name="severity"), nullable=False, index=True)

    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    instructions = Column(Text, nullable=True)  # Recomendaciones de seguridad

    # Geometría PostGIS — almacena polígonos, multipolígonos o puntos
    area = Column(Geometry("GEOMETRY", srid=4326), nullable=True)
    area_name = Column(String(500), nullable=True)

    # Límites temporales
    effective = Column(DateTime(timezone=True), nullable=True)  # Inicio del evento
    expires = Column(DateTime(timezone=True), nullable=True)    # Fin del evento

    # Metadatos
    source_url = Column(String(1000), nullable=True)
    raw_data = Column(JSONB, nullable=True)

    # Específico de terremotos (nulo para otros tipos)
    magnitude = Column(String(10), nullable=True)
    depth_km = Column(String(10), nullable=True)

    # Marcas de tiempo
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        Index("idx_events_active", "effective", "expires"),
        Index("idx_events_area", "area", postgresql_using="gist"),
    )

    def __repr__(self):
        return f"<Event {self.event_type.value} [{self.severity.value}] — {self.title[:50]}>"
