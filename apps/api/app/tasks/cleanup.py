"""Cleanup task — purges expired events and temporary data."""

import asyncio
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select, func
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.tasks.celery_app import celery_app
from app.config import get_settings
from app.models.event import Event

logger = logging.getLogger(__name__)
settings = get_settings()

# Days after expiration before purging the event
PURGE_AFTER_DAYS = 7

# Maximum events to purge per run (prevents long locks)
PURGE_BATCH_SIZE = 500


def _get_async_session() -> async_sessionmaker:
    engine = create_async_engine(settings.DATABASE_URL, pool_size=3)
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def _run_cleanup():
    """Purge events expired more than PURGE_AFTER_DAYS days ago."""
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

            # Purge in batch
            stmt = (
                delete(Event)
                .where(Event.expires < cutoff)
                .execution_options(synchronize_session=False)
            )
            result = await db.execute(stmt)
            deleted = result.rowcount
            await db.commit()

            logger.info("Cleanup: purged %d/%d expired events (cutoff: %s).", deleted, total, cutoff.isoformat())
            return deleted

        except Exception as e:
            await db.rollback()
            logger.exception("Error in cleanup task: %s", e)
            raise


@celery_app.task(name="app.tasks.cleanup.cleanup_expired_events", bind=True, max_retries=2)
def cleanup_expired_events(self):
    """Periodic purge of expired events from the database."""
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
        stmt = (
            select(Event.source, func.count(Event.id))
            .where(Event.created_at >= one_hour_ago)
            .group_by(Event.source)
        )
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
