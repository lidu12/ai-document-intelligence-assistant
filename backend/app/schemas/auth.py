"""Authentication & User Pydantic Schemas

Validates incoming registration/login payloads and defines outgoing user
and JWT token responses.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    """Schema for new user registration."""

    email: EmailStr = Field(..., description="User's valid email address")
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Plaintext password (minimum 8 characters)",
    )
    full_name: Optional[str] = Field(
        None,
        max_length=255,
        description="Optional full name or display name",
    )


class UserLogin(BaseModel):
    """Schema for user login credentials."""

    email: EmailStr = Field(..., description="Registered email address")
    password: str = Field(..., description="Account password")


class UserUpdate(BaseModel):
    """Schema for updating user profile information."""

    full_name: Optional[str] = Field(None, max_length=255)
    password: Optional[str] = Field(None, min_length=8, max_length=128)


class UserResponse(BaseModel):
    """Public schema for returning user profile data (never returns password)."""

    id: int
    email: EmailStr
    full_name: Optional[str] = None
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    """Schema for JWT access token responses."""

    access_token: str = Field(..., description="Signed JWT access token")
    token_type: str = Field(default="bearer", description="Token type prefix")


class TokenPayload(BaseModel):
    """Internal schema for decoded JWT payload claims."""

    sub: Optional[str] = None
    exp: Optional[int] = None
