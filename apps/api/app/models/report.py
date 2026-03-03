"""Modelo de Reporte Colaborativo — informes de tipo «Yo lo siento» por los usuarios."""

import uuid
from datetime import datetime

from geoalchemy2 import Geometry
from sqlalchemy import Column, String, DateTime, ForeignKey, func, Index
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class CollaborativeReport(Base):
    """Los usuarios informan en tiempo real de lo que están experimentando."""

    __tablename__ = "collaborative_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    event_id = Column(UUID(as_uuid=True), ForeignKey("events.id", ondelete="SET NULL"), nullable=True)

    report_type = Column(String(50), nullable=False)  # "rain", "wind", "hail", "smoke", "shaking"
    intensity = Column(String(20), nullable=False)     # "none", "light", "moderate", "strong", "extreme"
    location = Column(Geometry("POINT", srid=4326), nullable=False)
    comment = Column(String(500), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("idx_reports_user_id", "user_id"),
        Index("idx_reports_event_id", "event_id"),
        Index("idx_reports_created_at", "created_at"),
        Index("idx_reports_location", "location", postgresql_using="gist"),
    )

    def __repr__(self):
        return f"<Report {self.report_type} [{self.intensity}]>"
