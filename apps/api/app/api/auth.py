"""Authentication API — registration, login, and JWT tokens."""

from datetime import datetime, timedelta, timezone
from uuid import UUID

import jwt
from fastapi import APIRouter, Depends, HTTPException, Request
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user  # noqa: F401  # Re-export for compatibility
from app.config import get_settings
from app.database import get_db
from app.middleware import limiter
from app.models.user import User
from app.schemas import UserCreate, UserLogin, TokenOut

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _create_token(user_id: UUID) -> str:
    """Generate a JWT token for the user."""
    payload = {
        "sub": str(user_id),
        "exp": datetime.now(timezone.utc) + timedelta(hours=settings.JWT_EXPIRATION_HOURS),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def _verify_token(token: str) -> UUID:
    """Verify and decode a JWT token. Returns the user ID."""
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
    """Register a new user."""
    # Check if email already exists
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
    """Log in with email and password."""
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    if not user or not pwd_context.verify(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    return TokenOut(access_token=_create_token(user.id))
