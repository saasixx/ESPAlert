"""Async database engine, session factory, and Redis pool."""

import redis.asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

from app.config import get_settings

settings = get_settings()

# In testing we use NullPool to avoid 'Event loop is closed' when closing pytest
_is_testing = settings.ENVIRONMENT == "testing"

if _is_testing:
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DEBUG,
        poolclass=NullPool,
    )
else:
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DEBUG,
        pool_size=20,
        max_overflow=10,
        pool_recycle=1800,  # Recycle connections every 30 min
        pool_timeout=30,
        pool_pre_ping=True,  # Verify connections before using them
    )

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# ── Shared Redis pool ────────────────────────────────────────────────────────

redis_pool = aioredis.ConnectionPool.from_url(
    settings.REDIS_URL,
    max_connections=1 if _is_testing else 50,
    decode_responses=False,
)


def get_redis() -> aioredis.Redis:
    """Get a Redis client from the shared pool."""
    return aioredis.Redis(connection_pool=redis_pool)


class Base(DeclarativeBase):
    """Declarative base for all models."""


async def get_db() -> AsyncSession:  # type: ignore[misc]
    """FastAPI dependency — provides an async DB session."""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
