"""Authentication & Security Test Suite

Automated tests for user registration, duplicate email handling,
OAuth2 & JSON login token issuance, password hashing, and protected profile access.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password
from app.models.user import User


# ------------------------------------------------------------------------------
# 1. Password Cryptography Unit Tests
# ------------------------------------------------------------------------------
def test_password_hashing_and_verification():
    """Verifies that bcrypt correctly hashes and verifies plain passwords."""
    raw_password = "SecureSecretPassword123!"
    hashed = hash_password(raw_password)

    # Hash must be salted and non-empty
    assert hashed != raw_password
    assert len(hashed) > 20

    # Verification checks
    assert verify_password(raw_password, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False


# ------------------------------------------------------------------------------
# 2. User Registration Integration Tests
# ------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_register_user_success(client: AsyncClient):
    """Tests successful user registration returning a 201 Created response."""
    payload = {
        "email": "newuser@example.com",
        "password": "ValidPassword123!",
        "full_name": "New Developer",
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201

    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert data["full_name"] == "New Developer"
    assert data["is_active"] is True
    assert "id" in data
    assert "created_at" in data
    # Ensure sensitive password fields are never returned in responses
    assert "password" not in data
    assert "hashed_password" not in data


@pytest.mark.asyncio
async def test_register_duplicate_email_fails(client: AsyncClient, test_user: User):
    """Verifies that registering with an existing email returns 409 Conflict."""
    payload = {
        "email": test_user.email,  # Already registered in conftest fixture
        "password": "AnotherPassword123!",
        "full_name": "Imposter User",
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_register_invalid_email_fails(client: AsyncClient):
    """Verifies that invalid email formats are rejected with 422 Validation Error."""
    payload = {
        "email": "not-a-valid-email",
        "password": "Password123!",
        "full_name": "Invalid Email",
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 422


# ------------------------------------------------------------------------------
# 3. User Login Integration Tests (OAuth2 Form & JSON Body)
# ------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_login_oauth2_form_success(client: AsyncClient, test_user: User):
    """Tests standard OAuth2 form login returning a valid JWT access token."""
    form_data = {
        "username": test_user.email,
        "password": "Password123!",
    }
    response = await client.post("/api/v1/auth/login", data=form_data)
    assert response.status_code == 200

    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert len(data["access_token"]) > 20


@pytest.mark.asyncio
async def test_login_json_body_success(client: AsyncClient, test_user: User):
    """Tests JSON body login returning a valid JWT access token."""
    payload = {
        "email": test_user.email,
        "password": "Password123!",
    }
    response = await client.post("/api/v1/auth/login/json", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password_fails(client: AsyncClient, test_user: User):
    """Verifies that incorrect passwords return 401 Unauthorized."""
    payload = {
        "email": test_user.email,
        "password": "WrongPassword999!",
    }
    response = await client.post("/api/v1/auth/login/json", json=payload)
    assert response.status_code == 401
    assert "incorrect email or password" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_login_nonexistent_user_fails(client: AsyncClient):
    """Verifies that attempting to login with an unknown email returns 401 Unauthorized."""
    payload = {
        "email": "ghost@example.com",
        "password": "Password123!",
    }
    response = await client.post("/api/v1/auth/login/json", json=payload)
    assert response.status_code == 401


# ------------------------------------------------------------------------------
# 4. Protected Route & Token Validation Tests
# ------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_get_current_user_profile_success(client: AsyncClient, auth_headers: dict, test_user: User):
    """Verifies that an authenticated request with Bearer token retrieves user profile."""
    response = await client.get("/api/v1/auth/me", headers=auth_headers)
    assert response.status_code == 200

    data = response.json()
    assert data["id"] == test_user.id
    assert data["email"] == test_user.email
    assert data["full_name"] == test_user.full_name


@pytest.mark.asyncio
async def test_get_current_user_profile_without_token_fails(client: AsyncClient):
    """Verifies that unauthenticated requests to /auth/me return 401 Unauthorized."""
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_profile_with_invalid_token_fails(client: AsyncClient):
    """Verifies that forged or corrupted JWT tokens are rejected with 401 Unauthorized."""
    fake_headers = {"Authorization": "Bearer forged-fake-jwt-token-string"}
    response = await client.get("/api/v1/auth/me", headers=fake_headers)
    assert response.status_code == 401
