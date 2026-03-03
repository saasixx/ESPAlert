"""Modelo de Usuario — cuentas, zonas de interés y preferencias de notificación."""

import uuid
from datetime import datetime, time

from geoalchemy2 import Geometry
from sqlalchemy import (
    Column, String, DateTime, Time, Boolean,
    ForeignKey, func, Index,
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    """Cuenta de usuario con preferencias de notificación."""

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(320), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    display_name = Column(String(100), nullable=True)

    # Token de Firebase Cloud Messaging para notificaciones push
    fcm_token = Column(String(500), nullable=True)

    # Preferencias de notificación
    quiet_start = Column(Time, nullable=True)  # e.g. 23:00
    quiet_end = Column(Time, nullable=True)    # e.g. 07:00
    predictive_alerts = Column(Boolean, default=True)  # Alertas predictivas ("mañana habrá mal tiempo")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relaciones
    zones = relationship("UserZone", back_populates="user", cascade="all,delete-orphan")
    filters = relationship("UserFilter", back_populates="user", cascade="all,delete-orphan")

    def __repr__(self):
        return f"<User {self.email}>"


class UserZone(Base):
    """Zona geográfica de interés (casa, trabajo, ruta, etc.)."""

    __tablename__ = "user_zones"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    label = Column(String(100), nullable=False)  # "Casa", "Trabajo", "Ruta A-6"
    geometry = Column(Geometry("GEOMETRY", srid=4326), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="zones")

    __table_args__ = (
        Index("idx_user_zones_geom", "geometry", postgresql_using="gist"),
    )

    def __repr__(self):
        return f"<UserZone {self.label}>"


class UserFilter(Base):
    """Preferencias de filtrado de alertas por usuario."""

    __tablename__ = "user_filters"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Tipos de evento a recibir (NULL = todos)
    event_types = Column(ARRAY(String), nullable=True)
    # Severidad mínima para disparar notificación
    min_severity = Column(String(20), default="yellow")

    user = relationship("User", back_populates="filters")

    def __repr__(self):
        return f"<UserFilter types={self.event_types} min={self.min_severity}>"
