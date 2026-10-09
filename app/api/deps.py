"""API Dependencies (Dependency Injection)

Provides reusable FastAPI dependencies for async database sessions,
OAuth2 Bearer token extraction, and user authentication context.
"""

from typing import AsyncGenerator
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import async_session_factory
from app.core.exceptions import InactiveUserException, UnauthorizedException
from app.core.security import decode_access_token
from app.models.user import User
from app.services.auth_service import auth_service

# OAuth2 Password Bearer scheme points to the login endpoint for Swagger UI authorization
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login"
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that yields an async database session per request."""
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()


async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme),
) -> User:
    """Dependency that extracts, decodes, and validates the JWT token to fetch the current user."""
    payload = decode_access_token(token)
    if not payload:
        raise UnauthorizedException("Invalid or expired access token")

    user_id_str = payload.get("sub")
    if not user_id_str:
        raise UnauthorizedException("Token payload missing subject identifier")

    try:
        user_id = int(user_id_str)
    except ValueError:
        raise UnauthorizedException("Malformed user identifier in token")

    user = await auth_service.get_user_by_id(db, user_id=user_id)
    if not user:
        raise UnauthorizedException("User associated with this token no longer exists")

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Dependency ensuring that the authenticated user account is active."""
    if not current_user.is_active:
        raise InactiveUserException("User account is disabled")
    return current_user
