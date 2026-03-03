"""Celery app configuration."""

from celery import Celery
from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "espalert",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks.ingest", "app.tasks.cleanup"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Europe/Madrid",
    enable_utc=True,
    worker_concurrency=4,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
)

# Periodic beat schedule
celery_app.conf.beat_schedule = {
    "ingest-aemet": {
        "task": "app.tasks.ingest.ingest_aemet",
        "schedule": settings.AEMET_POLL_INTERVAL,
    },
    "ingest-ign": {
        "task": "app.tasks.ingest.ingest_ign",
        "schedule": settings.IGN_POLL_INTERVAL,
    },
    "ingest-dgt": {
        "task": "app.tasks.ingest.ingest_dgt",
        "schedule": settings.DGT_POLL_INTERVAL,
    },
    "ingest-meteoalarm": {
        "task": "app.tasks.ingest.ingest_meteoalarm",
        "schedule": settings.METEOALARM_POLL_INTERVAL,
    },
    "cleanup-expired": {
        "task": "app.tasks.cleanup.cleanup_expired_events",
        "schedule": 3600,  # Cada hora
    },
    "update-stats": {
        "task": "app.tasks.cleanup.update_source_stats",
        "schedule": 600,  # Cada 10 minutos
    },
}
