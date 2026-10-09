"""Authentication API Router

Provides HTTP REST endpoints for user registration, credential login,
and authenticated profile inspection.
"""

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_db
from app.models.user import User
from app.schemas.auth import Token, UserCreate, UserLogin, UserResponse
from app.services.auth_service import auth_service

router = APIRouter()


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
async def register(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> User:
    """Creates a new user account and returns the public user profile."""
    return await auth_service.register_user(db=db, user_in=user_in)


@router.post(
    "/login",
    response_model=Token,
    summary="Login with OAuth2 form data to obtain JWT access token",
)
async def login_oauth2(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
) -> Token:
    """Authenticates credentials using standard OAuth2 form format (compatible with Swagger UI)."""
    user = await auth_service.authenticate_user(
        db=db,
        email=form_data.username,
        password=form_data.password,
    )
    return auth_service.create_user_token(user)


@router.post(
    "/login/json",
    response_model=Token,
    summary="Login with JSON body to obtain JWT access token",
)
async def login_json(
    credentials: UserLogin,
    db: AsyncSession = Depends(get_db),
) -> Token:
    """Authenticates credentials using a standard JSON request body."""
    user = await auth_service.authenticate_user(
        db=db,
        email=credentials.email,
        password=credentials.password,
    )
    return auth_service.create_user_token(user)


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current authenticated user profile",
)
async def get_current_user_profile(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """Returns the profile details of the currently logged-in user."""
    return current_user
