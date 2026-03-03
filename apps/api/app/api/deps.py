"""Dependencias compartidas de la API — autenticación, BD, rate limiting."""

from uuid import UUID

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.models.user import User

settings = get_settings()
security = HTTPBearer()


def _verify_token(token: str) -> UUID:
    """Verifica y decodifica un token JWT. Retorna el ID del usuario."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return UUID(payload["sub"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Dependencia FastAPI: obtiene el usuario autenticado del token Bearer."""
    user_id = _verify_token(credentials.credentials)
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")
    return user
