"""Pydantic schemas for authentication and users."""

from datetime import datetime, time
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.schemas.common import PASSWORD_REGEX, sanitize_html


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    display_name: Optional[str] = Field(default=None, max_length=50)

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if not PASSWORD_REGEX.match(v):
            raise ValueError(
                "La contraseña debe tener al menos 8 caracteres, una mayúscula, una minúscula y un número."
            )
        return v

    @field_validator("display_name")
    @classmethod
    def sanitize_display_name(cls, v: Optional[str]) -> Optional[str]:
        if v:
            v = sanitize_html(v)
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(max_length=72)


class UserOut(BaseModel):
    id: UUID
    email: str
    display_name: Optional[str]
    quiet_start: Optional[time]
    quiet_end: Optional[time]
    predictive_alerts: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserSettingsUpdate(BaseModel):
    quiet_start: Optional[time] = None
    quiet_end: Optional[time] = None
    predictive_alerts: Optional[bool] = None
    fcm_token: Optional[str] = Field(default=None, max_length=256)
