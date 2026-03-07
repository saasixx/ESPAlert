"""Cleanup task — archives expired events then purges them from the live table."""

import asyncio
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select, func, text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.tasks.celery_app import celery_app
from app.config import get_settings
from app.models.event import Event

logger = logging.getLogger(__name__)
settings = get_settings()

# Roadmap spec: purge events older than 30 days
PURGE_AFTER_DAYS = 30

# Maximum events to process per run (prevents long locks)
PURGE_BATCH_SIZE = 500


def _get_async_session() -> async_sessionmaker:
    engine = create_async_engine(settings.DATABASE_URL, pool_size=3)
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def _run_cleanup():
    """Archive events expired > PURGE_AFTER_DAYS days ago, then delete them."""
    session_factory = _get_async_session()
    cutoff = datetime.now(timezone.utc) - timedelta(days=PURGE_AFTER_DAYS)

    async with session_factory() as db:
        try:
            # Count candidates
            count_stmt = select(func.count(Event.id)).where(Event.expires < cutoff)
            result = await db.execute(count_stmt)
            total = result.scalar() or 0

            if total == 0:
                logger.info("Cleanup: no expired events to purge.")
                return 0

            # Fetch IDs to process in this batch
            id_stmt = select(Event.id).where(Event.expires < cutoff).limit(PURGE_BATCH_SIZE)
            id_result = await db.execute(id_stmt)
            ids = [row[0] for row in id_result.all()]

            # Archive before deleting — INSERT … SELECT with ON CONFLICT DO NOTHING
            # (safe to re-run if a previous run failed mid-way)
            archive_stmt = text("""
                INSERT INTO events_archive (
                    id, source, source_id, event_type, severity, title, description,
                    instructions, area, area_name, effective, expires, source_url,
                    raw_data, magnitude, depth_km, created_at, updated_at, archived_at
                )
                SELECT
                    id, source, source_id, event_type, severity, title, description,
                    instructions, area, area_name, effective, expires, source_url,
                    raw_data, magnitude, depth_km, created_at, updated_at, now()
                FROM events
                WHERE id = ANY(:ids)
                ON CONFLICT (id) DO NOTHING
            """)
            await db.execute(archive_stmt, {"ids": ids})

            # Delete from live table
            del_stmt = (
                delete(Event)
                .where(Event.id.in_(ids))
                .execution_options(synchronize_session=False)
            )
            del_result = await db.execute(del_stmt)
            deleted = del_result.rowcount
            await db.commit()

            logger.info(
                "Cleanup: archived and purged %d/%d expired events (cutoff: %s).",
                deleted,
                total,
                cutoff.isoformat(),
            )
            return deleted

        except Exception as e:
            await db.rollback()
            logger.exception("Error in cleanup task: %s", e)
            raise


@celery_app.task(name="app.tasks.cleanup.cleanup_expired_events", bind=True, max_retries=2)
def cleanup_expired_events(self):
    """Periodic task: archive then purge expired events from the database."""
    try:
        deleted = asyncio.run(_run_cleanup())
        return {"deleted": deleted}
    except Exception as exc:
        logger.exception("Cleanup task failed: %s", exc)
        self.retry(exc=exc, countdown=300)


async def _update_source_stats():
    """Update ingestion statistics by source in Redis."""
    from app.database import get_redis

    session_factory = _get_async_session()
    redis = get_redis()

    async with session_factory() as db:
        now = datetime.now(timezone.utc)
        one_hour_ago = now - timedelta(hours=1)

        # Count recent events by source
        stmt = select(Event.source, func.count(Event.id)).where(Event.created_at >= one_hour_ago).group_by(Event.source)
        result = await db.execute(stmt)

        stats = {}
        for row in result.all():
            source_val = row[0].value if hasattr(row[0], "value") else str(row[0])
            stats[source_val] = row[1]

        # Store in Redis with 10-minute TTL
        import json

        await redis.set("espalert:stats:ingest_1h", json.dumps(stats), ex=600)
        logger.debug("Ingestion stats updated: %s", stats)


@celery_app.task(name="app.tasks.cleanup.update_source_stats")
def update_source_stats():
    """Update ingestion statistics by source."""
    try:
        asyncio.run(_update_source_stats())
    except Exception as exc:
        logger.warning("Error updating stats: %s", exc)
