"""Celery ingestion tasks — periodic fetching from all data sources."""

import asyncio
import logging

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.tasks.celery_app import celery_app
from app.config import get_settings
from app.connectors.aemet import AemetConnector
from app.connectors.ign import IGNConnector
from app.connectors.dgt import DGTConnector
from app.connectors.meteoalarm import MeteoAlarmConnector
from app.services.normalizer import Normalizer
from app.services.geo_engine import GeoEngine
from app.services.notification import NotificationService

logger = logging.getLogger(__name__)
settings = get_settings()


def _get_async_session() -> async_sessionmaker:
    """Create a fresh async session factory for Celery workers."""
    engine = create_async_engine(settings.DATABASE_URL, pool_size=5)
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def _process_events(raw_events: list[dict]):
    """Normalize events, find affected users, and send notifications."""
    session_factory = _get_async_session()

    async with session_factory() as db:
        try:
            normalizer = Normalizer(db)
            new_events = await normalizer.process_events(raw_events)

            if new_events:
                geo_engine = GeoEngine(db)
                notifier = NotificationService()

                for event in new_events:
                    affected = await geo_engine.find_affected_users(event)
                    if affected:
                        await notifier.notify_users(event, affected)

                await db.commit()
            else:
                await db.commit()

        except Exception as e:
            await db.rollback()
            logger.exception(f"Error processing events: {e}")
            raise


@celery_app.task(name="app.tasks.ingest.ingest_aemet", bind=True, max_retries=3)
def ingest_aemet(self):
    """Fetch and process AEMET weather warnings."""
    try:
        connector = AemetConnector()
        raw_events = asyncio.run(connector.fetch_warnings())
        if raw_events:
            asyncio.run(_process_events(raw_events))
        logger.info(f"AEMET ingestion complete: {len(raw_events)} events")
    except Exception as exc:
        logger.exception(f"AEMET ingestion failed: {exc}")
        self.retry(exc=exc, countdown=60)


@celery_app.task(name="app.tasks.ingest.ingest_ign", bind=True, max_retries=3)
def ingest_ign(self):
    """Fetch and process IGN earthquake data."""
    try:
        connector = IGNConnector()
        raw_events = asyncio.run(connector.fetch_earthquakes())
        if raw_events:
            asyncio.run(_process_events(raw_events))
        logger.info(f"IGN ingestion complete: {len(raw_events)} earthquakes")
    except Exception as exc:
        logger.exception(f"IGN ingestion failed: {exc}")
        self.retry(exc=exc, countdown=30)


@celery_app.task(name="app.tasks.ingest.ingest_dgt", bind=True, max_retries=3)
def ingest_dgt(self):
    """Fetch and process DGT traffic incidents."""
    try:
        connector = DGTConnector()
        raw_events = asyncio.run(connector.fetch_incidents())
        if raw_events:
            asyncio.run(_process_events(raw_events))
        logger.info(f"DGT ingestion complete: {len(raw_events)} incidents")
    except Exception as exc:
        logger.exception(f"DGT ingestion failed: {exc}")
        self.retry(exc=exc, countdown=60)


@celery_app.task(name="app.tasks.ingest.ingest_meteoalarm", bind=True, max_retries=3)
def ingest_meteoalarm(self):
    """Fetch and process MeteoAlarm warnings."""
    try:
        connector = MeteoAlarmConnector()
        raw_events = asyncio.run(connector.fetch_warnings())
        if raw_events:
            asyncio.run(_process_events(raw_events))
        logger.info(f"MeteoAlarm ingestion complete: {len(raw_events)} warnings")
    except Exception as exc:
        logger.exception(f"MeteoAlarm ingestion failed: {exc}")
        self.retry(exc=exc, countdown=60)


@celery_app.task(name="app.tasks.ingest.ingest_all")
def ingest_all():
    """Run all ingestion tasks at once (useful for initial load)."""
    ingest_aemet.delay()
    ingest_ign.delay()
    ingest_dgt.delay()
    ingest_meteoalarm.delay()
