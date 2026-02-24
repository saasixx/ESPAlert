"""Database engine, session factory, and Redis connection pool."""

import redis.asyncio as aioredis
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from app.config import get_settings

settings = get_settings()

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=20,
    max_overflow=10,
    pool_recycle=1800,  # Recycle connections after 30 min
    pool_timeout=30,
    pool_pre_ping=True,  # Verify connections before use
)

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# ── Shared Redis connection pool ─────────────────────────────────────────────

redis_pool = aioredis.ConnectionPool.from_url(
    settings.REDIS_URL,
    max_connections=50,
    decode_responses=False,
)


def get_redis() -> aioredis.Redis:
    """Get a Redis client from the shared connection pool."""
    return aioredis.Redis(connection_pool=redis_pool)


class Base(DeclarativeBase):
    """Declarative base for all models."""
    pass


async def get_db() -> AsyncSession:
    """FastAPI dependency — yields an async DB session."""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
