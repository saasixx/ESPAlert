"""Motor de base de datos asíncrono, fábrica de sesiones y pool de Redis."""

import redis.asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

from app.config import get_settings

settings = get_settings()

# En testing usamos NullPool para evitar 'Event loop is closed' al cerrar pytest
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
        pool_recycle=1800,   # Reciclar conexiones cada 30 min
        pool_timeout=30,
        pool_pre_ping=True,  # Verificar conexiones antes de usarlas
    )

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# ── Pool compartido de Redis ─────────────────────────────────────────────────

redis_pool = aioredis.ConnectionPool.from_url(
    settings.REDIS_URL,
    max_connections=1 if _is_testing else 50,
    decode_responses=False,
)


def get_redis() -> aioredis.Redis:
    """Obtiene un cliente Redis del pool compartido."""
    return aioredis.Redis(connection_pool=redis_pool)


class Base(DeclarativeBase):
    """Base declarativa para todos los modelos."""


async def get_db() -> AsyncSession:  # type: ignore[misc]
    """Dependencia de FastAPI — proporciona una sesión de BD asíncrona."""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
