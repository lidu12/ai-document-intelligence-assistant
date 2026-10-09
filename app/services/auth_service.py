"""Authentication & User Management Service

Coordinates user registration, bcrypt password hashing, credential verification,
and JWT access token issuance.
"""

from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    InactiveUserException,
    InvalidCredentialsException,
    UserAlreadyExistsException,
)
from app.core.security import create_access_token, get_password_hash, verify_password
from app.models.user import User
from app.schemas.auth import Token, UserCreate


class AuthService:
    """Handles business logic for user accounts and authentication."""

    @staticmethod
    async def register_user(db: AsyncSession, user_in: UserCreate) -> User:
        """Registers a new user account if the email is not already taken.

        Args:
            db: Active async database session.
            user_in: UserCreate schema with email, password, and full name.

        Returns:
            User: The newly created User database record.

        Raises:
            UserAlreadyExistsException: If email is already registered.
        """
        # Check if email is already in use
        query = select(User).where(User.email == user_in.email.lower().strip())
        result = await db.execute(query)
        existing_user = result.scalar_one_or_none()

        if existing_user:
            raise UserAlreadyExistsException()

        # Hash password and store record
        user = User(
            email=user_in.email.lower().strip(),
            hashed_password=get_password_hash(user_in.password),
            full_name=user_in.full_name,
            is_active=True,
            is_superuser=False,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def authenticate_user(
        db: AsyncSession,
        email: str,
        password: str,
    ) -> User:
        """Authenticates a user by email and password.

        Args:
            db: Active async database session.
            email: User's login email.
            password: User's plaintext password.

        Returns:
            User: Authenticated User record.

        Raises:
            InvalidCredentialsException: If user not found or password incorrect.
            InactiveUserException: If user account is disabled.
        """
        query = select(User).where(User.email == email.lower().strip())
        result = await db.execute(query)
        user = result.scalar_one_or_none()

        if not user or not verify_password(password, user.hashed_password):
            raise InvalidCredentialsException()

        if not user.is_active:
            raise InactiveUserException()

        return user

    @staticmethod
    def create_user_token(user: User) -> Token:
        """Issues a signed JWT access token for an authenticated user."""
        token_str = create_access_token(subject=user.id)
        return Token(access_token=token_str, token_type="bearer")

    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
        """Fetches a user by primary key ID."""
        query = select(User).where(User.id == user_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()


# Singleton instance
auth_service = AuthService()
