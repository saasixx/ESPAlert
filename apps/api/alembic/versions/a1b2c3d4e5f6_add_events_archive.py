"""add events_archive table

Revision ID: a1b2c3d4e5f6
Revises: 2c2a65c79331
Create Date: 2026-03-07 00:00:00.000000
"""

from typing import Sequence, Union

import geoalchemy2
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "2c2a65c79331"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "events_archive",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "source",
            postgresql.ENUM("AEMET", "IGN", "DGT", "METEOALARM", "ESALERT", name="event_source", create_type=False),
            nullable=False,
        ),
        sa.Column("source_id", sa.String(length=255), nullable=False),
        sa.Column(
            "event_type",
            postgresql.ENUM(
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
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "severity",
            postgresql.ENUM("GREEN", "YELLOW", "ORANGE", "RED", name="severity", create_type=False),
            nullable=False,
        ),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("instructions", sa.Text(), nullable=True),
        sa.Column(
            "area",
            geoalchemy2.types.Geometry(srid=4326, from_text="ST_GeomFromEWKT", name="geometry"),
            nullable=True,
        ),
        sa.Column("area_name", sa.String(length=500), nullable=True),
        sa.Column("effective", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source_url", sa.String(length=1000), nullable=True),
        sa.Column("raw_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("magnitude", sa.String(length=10), nullable=True),
        sa.Column("depth_km", sa.String(length=10), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        # Archive-specific
        sa.Column(
            "archived_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_archive_source_id", "events_archive", ["source_id"], unique=False)
    op.create_index("idx_archive_expires", "events_archive", ["expires"], unique=False)
    op.create_index("idx_archive_archived_at", "events_archive", ["archived_at"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_archive_archived_at", table_name="events_archive")
    op.drop_index("idx_archive_expires", table_name="events_archive")
    op.drop_index("idx_archive_source_id", table_name="events_archive")
    op.drop_table("events_archive")
