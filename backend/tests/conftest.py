"""Pytest Fixtures & Test Configuration

Provides async test database sessions, HTTP test client with dependency overrides,
pre-authenticated JWT fixtures, and offline Google Gemini AI mock interceptors.
"""

import asyncio
import os
import sys
from typing import AsyncGenerator, Dict, Generator
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

# Ensure backend directory is on Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Configure test environment variables prior to importing application modules
os.environ["ENVIRONMENT"] = "testing"
os.environ["DEBUG"] = "False"
os.environ["SECRET_KEY"] = "test-secret-key-32-chars-long-for-testing-only-12345"
os.environ["GEMINI_API_KEY"] = "mock-gemini-api-key-for-unit-tests"

from pgvector.sqlalchemy import Vector
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.ext.compiler import compiles

from app.api.deps import get_db
from app.core.security import create_access_token, hash_password
from app.main import app
from app.models.base import Base
from app.models.user import User


# ------------------------------------------------------------------------------
# 1. SQLite Adapter for pgvector Vector Columns
# ------------------------------------------------------------------------------
# SQLite does not natively support pgvector's Vector type.
# We instruct SQLAlchemy to compile Vector(n) as TEXT during SQLite test execution.
@compiles(Vector, "sqlite")
def compile_vector_sqlite(type_, compiler, **kw) -> str:
    return "TEXT"


# ------------------------------------------------------------------------------
# 2. In-Memory Async Database Engine for Testing
# ------------------------------------------------------------------------------
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine: AsyncEngine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

TestingSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


import pytest_asyncio

# ------------------------------------------------------------------------------
# 3. Database Fixtures
# ------------------------------------------------------------------------------
@pytest_asyncio.fixture(scope="function")
async def test_db() -> AsyncGenerator[AsyncSession, None]:
    """Yields a fresh, isolated database session with all tables created in-memory."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestingSessionLocal() as session:
        yield session
        await session.rollback()

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


# ------------------------------------------------------------------------------
# 4. Async HTTP Test Client with FastAPI Dependency Overrides
# ------------------------------------------------------------------------------
@pytest_asyncio.fixture(scope="function")
async def client(test_db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Creates an AsyncClient that communicates directly with FastAPI using test_db."""
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield test_db

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


# ------------------------------------------------------------------------------
# 5. User & Authentication Fixtures
# ------------------------------------------------------------------------------
@pytest_asyncio.fixture(scope="function")
async def test_user(test_db: AsyncSession) -> User:
    """Creates and inserts a standard verified active user into the test database."""
    user = User(
        email="testuser@example.com",
        hashed_password=hash_password("Password123!"),
        full_name="Test Developer",
        is_active=True,
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    return user


@pytest_asyncio.fixture(scope="function")
async def auth_headers(test_user: User) -> Dict[str, str]:
    """Generates valid Bearer Authorization HTTP headers for the test user."""
    access_token = create_access_token(subject=test_user.id)
    return {"Authorization": f"Bearer {access_token}"}


@pytest_asyncio.fixture(scope="function")
async def second_test_user(test_db: AsyncSession) -> User:
    """Creates a second distinct user to test multi-tenant document authorization."""
    user = User(
        email="seconduser@example.com",
        hashed_password=hash_password("Password123!"),
        full_name="Second User",
        is_active=True,
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    return user


@pytest_asyncio.fixture(scope="function")
async def second_auth_headers(second_test_user: User) -> Dict[str, str]:
    """Generates Bearer Authorization HTTP headers for the second user."""
    access_token = create_access_token(subject=second_test_user.id)
    return {"Authorization": f"Bearer {access_token}"}


# ------------------------------------------------------------------------------
# 6. Mock Google Gemini AI Services (Embeddings & Generation)
# ------------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def mock_gemini_services():
    """Automatically mocks all Gemini API network calls during test runs.

    - Embeddings: Returns deterministic 768-dimensional float vectors.
    - AI Chat: Returns a grounded answer string.
    """
    mock_vector = [0.05] * 768

    def mock_batch_embeddings(texts, batch_size=50):
        return [[0.05] * 768 for _ in texts]

    with patch(
        "app.services.embedding_service.EmbeddingService.get_query_embedding",
        return_value=mock_vector,
    ), patch(
        "app.services.embedding_service.EmbeddingService.get_document_embeddings_batch",
        side_effect=mock_batch_embeddings,
    ), patch(
        "app.services.ai_service.AIService.generate_grounded_answer",
        new_callable=AsyncMock,
        return_value="This is a verified test answer grounded in the uploaded document.",
    ), patch(
        "app.services.rag_service.vector_service.search_similar_chunks",
        new_callable=AsyncMock,
        return_value=[],
    ):
        yield
