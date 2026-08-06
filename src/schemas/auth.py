"""Pydantic schemas for authentication and user records."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    """Signup payload for a new (customer) user."""

    email: EmailStr
    password: str = Field(min_length=6, max_length=128)


class UserOut(BaseModel):
    """A user as returned by the API (never includes the password)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    role: str
    created_at: datetime


class Token(BaseModel):
    """The JWT returned on successful login."""

    access_token: str
    token_type: str = "bearer"
