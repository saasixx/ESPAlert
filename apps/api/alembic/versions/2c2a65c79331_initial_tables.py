"""initial tables

Revision ID: 2c2a65c79331
Revises:
Create Date: 2026-02-24 17:27:15.081782
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
import geoalchemy2
from sqlalchemy.dialects import postgresql

revision: str = "2c2a65c79331"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "events",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "source", sa.Enum("AEMET", "IGN", "DGT", "METEOALARM", "ESALERT", name="event_source"), nullable=False
        ),
        sa.Column("source_id", sa.String(length=255), nullable=False),
        sa.Column(
            "event_type",
            sa.Enum(
                "WIND",
                "RAIN",
                "STORM",
                "SNOW",
                "ICE",
                "FOG",
                "HEAT",
                "COLD",
                "UV",
                "FIRE_RISK",
                "COASTAL",
                "WAVE",
                "TIDE",
                "EARTHQUAKE",
                "TSUNAMI",
                "TRAFFIC_ACCIDENT",
                "TRAFFIC_CLOSURE",
                "TRAFFIC_WORKS",
                "TRAFFIC_JAM",
                "CIVIL_PROTECTION",
                "OTHER",
                name="event_type",
            ),
            nullable=False,
        ),
        sa.Column("severity", sa.Enum("GREEN", "YELLOW", "ORANGE", "RED", name="severity"), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("instructions", sa.Text(), nullable=True),
        sa.Column(
            "area", geoalchemy2.types.Geometry(srid=4326, from_text="ST_GeomFromEWKT", name="geometry"), nullable=True
        ),
        sa.Column("area_name", sa.String(length=500), nullable=True),
        sa.Column("effective", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source_url", sa.String(length=1000), nullable=True),
        sa.Column("raw_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("magnitude", sa.String(length=10), nullable=True),
        sa.Column("depth_km", sa.String(length=10), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("source_id"),
    )
    op.create_index("idx_events_active", "events", ["effective", "expires"], unique=False)
    # idx_events_area GiST index auto-created by geoalchemy2
    op.create_index(op.f("ix_events_event_type"), "events", ["event_type"], unique=False)
    op.create_index(op.f("ix_events_severity"), "events", ["severity"], unique=False)
    op.create_index(op.f("ix_events_source"), "events", ["source"], unique=False)

    op.create_table(
        "users",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("display_name", sa.String(length=100), nullable=True),
        sa.Column("fcm_token", sa.String(length=500), nullable=True),
        sa.Column("quiet_start", sa.Time(), nullable=True),
        sa.Column("quiet_end", sa.Time(), nullable=True),
        sa.Column("predictive_alerts", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    op.create_table(
        "collaborative_reports",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=True),
        sa.Column("event_id", sa.UUID(), nullable=True),
        sa.Column("report_type", sa.String(length=50), nullable=False),
        sa.Column("intensity", sa.String(length=20), nullable=False),
        sa.Column(
            "location",
            geoalchemy2.types.Geometry(
                geometry_type="POINT", srid=4326, from_text="ST_GeomFromEWKT", name="geometry", nullable=False
            ),
            nullable=False,
        ),
        sa.Column("comment", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    # idx_collaborative_reports_location GiST index auto-created by geoalchemy2
    op.create_index("idx_reports_created_at", "collaborative_reports", ["created_at"], unique=False)
    op.create_index("idx_reports_event_id", "collaborative_reports", ["event_id"], unique=False)
    op.create_index("idx_reports_user_id", "collaborative_reports", ["user_id"], unique=False)

    op.create_table(
        "user_filters",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("event_types", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("min_severity", sa.String(length=20), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "user_zones",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("label", sa.String(length=100), nullable=False),
        sa.Column(
            "geometry",
            geoalchemy2.types.Geometry(srid=4326, from_text="ST_GeomFromEWKT", name="geometry", nullable=False),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    # idx_user_zones_geometry GiST index auto-created by geoalchemy2


def downgrade() -> None:
    op.drop_table("user_zones")
    op.drop_table("user_filters")
    op.drop_index("idx_reports_user_id", table_name="collaborative_reports")
    op.drop_index("idx_reports_event_id", table_name="collaborative_reports")
    op.drop_index("idx_reports_created_at", table_name="collaborative_reports")
    op.drop_table("collaborative_reports")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
    op.drop_index(op.f("ix_events_source"), table_name="events")
    op.drop_index(op.f("ix_events_severity"), table_name="events")
    op.drop_index(op.f("ix_events_event_type"), table_name="events")
    op.drop_index("idx_events_active", table_name="events")
    op.drop_table("events")
