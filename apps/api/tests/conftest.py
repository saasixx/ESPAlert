"""Test configuration and fixtures."""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from app.main import app

# Todos los tests async usan un unico event loop de sesion
pytestmark = pytest.mark.asyncio(loop_scope="session")


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def client():
    """Async HTTP client for testing FastAPI endpoints."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture(scope="session", autouse=True, loop_scope="session")
async def _cleanup_connections():
    """Limpiar engine de BD y pool de Redis al finalizar los tests."""
    yield
    from app.database import engine, redis_pool

    await engine.dispose()
    await redis_pool.disconnect()
