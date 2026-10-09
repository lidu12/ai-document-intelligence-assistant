"""Database Engine & Async Session Management

Configures the asynchronous SQLAlchemy engine, connection pooling,
session factory, and database dependency for FastAPI request lifecycles.
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy import text

from app.core.config import settings

# ------------------------------------------------------------------------------
# 1. Asynchronous SQLAlchemy Engine
# Configure connect_args for asyncpg compatibility with cloud poolers (e.g. Supabase, PgBouncer)
connect_args = {}
if "asyncpg" in settings.DATABASE_URL:
    connect_args["statement_cache_size"] = 0

engine: AsyncEngine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DATABASE_ECHO_SQL,  # Logs SQL statements if enabled in settings
    future=True,                      # Use SQLAlchemy 2.0 style APIs
    pool_pre_ping=True,               # Tests connections before using them to prevent stale connection errors
    pool_size=10,                     # Maximum number of permanent connections in the pool
    max_overflow=20,                  # Additional temporary connections allowed during traffic spikes
    connect_args=connect_args,
)

# ------------------------------------------------------------------------------
# 2. Async Session Factory
# ------------------------------------------------------------------------------
# async_sessionmaker creates new AsyncSession instances for each database transaction.
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,  # Prevents attributes from expiring after commit (essential for async)
)
async_session_factory = AsyncSessionLocal


# ------------------------------------------------------------------------------
# 3. Database Dependency for FastAPI
# ------------------------------------------------------------------------------
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an asynchronous database session.

    Guarantees that each request gets its own session and that the session
    is properly closed when the request finishes, even if exceptions occur.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ------------------------------------------------------------------------------
# 4. Database Helper Functions
# ------------------------------------------------------------------------------
async def init_db_extensions() -> None:
    """Initializes necessary PostgreSQL extensions, specifically 'pgvector'."""
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
