"""API de Autenticación — registro, inicio de sesión y tokens JWT."""

from datetime import datetime, timedelta, timezone
from uuid import UUID

import jwt
from fastapi import APIRouter, Depends, HTTPException, Request
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user  # noqa: F401  # Re-exportar para compatibilidad
from app.config import get_settings
from app.database import get_db
from app.middleware import limiter
from app.models.user import User
from app.schemas import UserCreate, UserLogin, TokenOut

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _create_token(user_id: UUID) -> str:
    """Genera un token JWT para el usuario."""
    payload = {
        "sub": str(user_id),
        "exp": datetime.now(timezone.utc) + timedelta(hours=settings.JWT_EXPIRATION_HOURS),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def _verify_token(token: str) -> UUID:
    """Verifica y decodifica un token JWT. Retorna el ID del usuario."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return UUID(payload["sub"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")


@router.post("/register", response_model=TokenOut, status_code=201)
@limiter.limit(settings.RATE_LIMIT_AUTH)
async def register(request: Request, data: UserCreate, db: AsyncSession = Depends(get_db)):
    """Registra un nuevo usuario."""
    # Verificar si el email ya existe
    existing = await db.execute(select(User).where(User.email == data.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="El email ya está registrado")

    user = User(
        email=data.email,
        password_hash=pwd_context.hash(data.password),
        display_name=data.display_name,
    )
    db.add(user)
    await db.flush()

    return TokenOut(access_token=_create_token(user.id))


@router.post("/login", response_model=TokenOut)
@limiter.limit(settings.RATE_LIMIT_AUTH)
async def login(request: Request, data: UserLogin, db: AsyncSession = Depends(get_db)):
    """Inicia sesión con email y contraseña."""
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    if not user or not pwd_context.verify(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    return TokenOut(access_token=_create_token(user.id))
