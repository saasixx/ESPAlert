"""Tarea de limpieza — purga eventos expirados y datos temporales."""

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

# Días tras la expiración antes de purgar el evento
PURGE_AFTER_DAYS = 7

# Máximo de eventos a purgar por ejecución (evita bloqueos largos)
PURGE_BATCH_SIZE = 500


def _get_async_session() -> async_sessionmaker:
    engine = create_async_engine(settings.DATABASE_URL, pool_size=3)
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def _run_cleanup():
    """Purga eventos expirados hace más de PURGE_AFTER_DAYS días."""
    session_factory = _get_async_session()
    cutoff = datetime.now(timezone.utc) - timedelta(days=PURGE_AFTER_DAYS)

    async with session_factory() as db:
        try:
            # Contar candidatos
            count_stmt = select(func.count(Event.id)).where(Event.expires < cutoff)
            result = await db.execute(count_stmt)
            total = result.scalar() or 0

            if total == 0:
                logger.info("Limpieza: no hay eventos expirados para purgar.")
                return 0

            # Purgar en lote
            stmt = (
                delete(Event)
                .where(Event.expires < cutoff)
                .execution_options(synchronize_session=False)
            )
            result = await db.execute(stmt)
            deleted = result.rowcount
            await db.commit()

            logger.info("Limpieza: purgados %d/%d eventos expirados (corte: %s).", deleted, total, cutoff.isoformat())
            return deleted

        except Exception as e:
            await db.rollback()
            logger.exception("Error en tarea de limpieza: %s", e)
            raise


@celery_app.task(name="app.tasks.cleanup.cleanup_expired_events", bind=True, max_retries=2)
def cleanup_expired_events(self):
    """Purga periódica de eventos expirados de la base de datos."""
    try:
        deleted = asyncio.run(_run_cleanup())
        return {"deleted": deleted}
    except Exception as exc:
        logger.exception("Tarea de limpieza falló: %s", exc)
        self.retry(exc=exc, countdown=300)


async def _update_source_stats():
    """Actualiza estadísticas de ingesta por fuente en Redis."""
    from app.database import get_redis

    session_factory = _get_async_session()
    redis = get_redis()

    async with session_factory() as db:
        now = datetime.now(timezone.utc)
        one_hour_ago = now - timedelta(hours=1)

        # Contar eventos recientes por fuente
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

        # Guardar en Redis con TTL de 10 minutos
        import json

        await redis.set("espalert:stats:ingest_1h", json.dumps(stats), ex=600)
        logger.debug("Estadísticas de ingesta actualizadas: %s", stats)


@celery_app.task(name="app.tasks.cleanup.update_source_stats")
def update_source_stats():
    """Actualiza estadísticas de ingesta por fuente."""
    try:
        asyncio.run(_update_source_stats())
    except Exception as exc:
        logger.warning("Error actualizando estadísticas: %s", exc)
