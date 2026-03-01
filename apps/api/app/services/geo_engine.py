"""Geo-intersection engine — finds users affected by an event area."""

import logging
from datetime import datetime, timezone

from sqlalchemy import select, and_, text
from sqlalchemy.ext.asyncio import AsyncSession
from geoalchemy2.functions import ST_Intersects

from app.models.event import Event, Severity
from app.models.user import User, UserZone, UserFilter

logger = logging.getLogger(__name__)

# Severity ordering for comparison
SEVERITY_ORDER = {
    Severity.GREEN: 0,
    Severity.YELLOW: 1,
    Severity.ORANGE: 2,
    Severity.RED: 3,
}
SEVERITY_STR_ORDER = {s.value: i for s, i in SEVERITY_ORDER.items()}


class GeoEngine:
    """
    Uses PostGIS to determine which users are affected by an event
    based on their configured zones, filters, and quiet hours.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def find_affected_users(self, event: Event) -> list[dict]:
        """
        Find all users whose zones intersect the event area
        and whose filters match the event type/severity.

        Returns list of dicts: {user_id, email, fcm_token, zone_label}
        """
        if event.area is None:
            return []

        now = datetime.now(timezone.utc).time()

        # Raw SQL for complex PostGIS + filter + quiet hours query
        query = text("""
            SELECT DISTINCT
                u.id AS user_id,
                u.email,
                u.fcm_token,
                uz.label AS zone_label
            FROM user_zones uz
            JOIN users u ON u.id = uz.user_id
            LEFT JOIN user_filters uf ON uf.user_id = u.id
            WHERE ST_Intersects(uz.geometry, (
                SELECT area FROM events WHERE id = :event_id
            ))
            AND u.fcm_token IS NOT NULL
            AND (
                uf.id IS NULL  -- No filter = receive all
                OR (
                    (uf.event_types IS NULL OR :event_type = ANY(uf.event_types))
                    AND (
                        :severity_order >= CASE uf.min_severity
                            WHEN 'green' THEN 0
                            WHEN 'yellow' THEN 1
                            WHEN 'orange' THEN 2
                            WHEN 'red' THEN 3
                            ELSE 1
                        END
                    )
                )
            )
            AND (
                u.quiet_start IS NULL
                OR u.quiet_end IS NULL
                OR NOT (
                    CASE
                        WHEN u.quiet_start <= u.quiet_end
                        THEN :current_time BETWEEN u.quiet_start AND u.quiet_end
                        ELSE :current_time >= u.quiet_start OR :current_time <= u.quiet_end
                    END
                )
            )
        """)

        event_severity = SEVERITY_STR_ORDER.get(
            event.severity.value if event.severity else "green", 0
        )
        event_type_val = event.event_type.value if event.event_type else "other"

        result = await self.db.execute(query, {
            "event_id": str(event.id),
            "event_type": event_type_val,
            "severity_order": event_severity,
            "current_time": now,
        })

        affected = []
        for row in result.fetchall():
            affected.append({
                "user_id": str(row.user_id),
                "email": row.email,
                "fcm_token": row.fcm_token,
                "zone_label": row.zone_label,
            })

        logger.info(f"GeoEngine: event {event.source_id} affects {len(affected)} users")
        return affected
