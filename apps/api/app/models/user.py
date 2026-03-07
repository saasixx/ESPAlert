"""User model — accounts, zones of interest, and notification preferences."""

import uuid

from geoalchemy2 import Geometry
from sqlalchemy import (
    Column,
    String,
    DateTime,
    Time,
    Boolean,
    ForeignKey,
    func,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    """User account with notification preferences."""

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(320), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    display_name = Column(String(100), nullable=True)

    # Firebase Cloud Messaging token for push notifications
    fcm_token = Column(String(500), nullable=True)
    
    # Telegram Chat ID for notifications
    telegram_chat_id = Column(String(100), nullable=True, index=True)

    # Notification preferences
    quiet_start = Column(Time, nullable=True)  # e.g. 23:00
    quiet_end = Column(Time, nullable=True)  # e.g. 07:00
    predictive_alerts = Column(Boolean, default=True)  # Predictive alerts ("tomorrow will have bad weather")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    zones = relationship("UserZone", back_populates="user", cascade="all,delete-orphan")
    filters = relationship("UserFilter", back_populates="user", cascade="all,delete-orphan")

    def __repr__(self):
        return f"<User {self.email}>"


class UserZone(Base):
    """Geographic zone of interest (home, work, route, etc.)."""

    __tablename__ = "user_zones"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    label = Column(String(100), nullable=False)  # "Home", "Work", "Route A-6"
    geometry = Column(Geometry("GEOMETRY", srid=4326), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="zones")

    __table_args__ = (Index("idx_user_zones_geom", "geometry", postgresql_using="gist"),)

    def __repr__(self):
        return f"<UserZone {self.label}>"


class UserFilter(Base):
    """Alert filtering preferences per user."""

    __tablename__ = "user_filters"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Event types to receive (NULL = all)
    event_types = Column(ARRAY(String), nullable=True)
    # Minimum severity to trigger notification
    min_severity = Column(String(20), default="yellow")

    user = relationship("User", back_populates="filters")

    def __repr__(self):
        return f"<UserFilter types={self.event_types} min={self.min_severity}>"
