"""FastAPI Application Entry Point

The central application module that initializes the FastAPI instance,
configures CORS middleware, registers domain exception handlers, manages
async database lifespan events, and mounts all REST API routers.
"""

from contextlib import asynccontextmanager
import logging
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.api.routes import auth_router, chat_router, documents_router
from app.core.config import settings
from app.core.database import engine, init_db_extensions
from app.core.exceptions import AppException
from app.models.base import Base
# Import all models to ensure they are registered on Base.metadata for table creation
import app.models  # noqa: F401

# ------------------------------------------------------------------------------
# 1. Logging Configuration
# ------------------------------------------------------------------------------
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("doc_intelligence")


# ------------------------------------------------------------------------------
# 2. Application Lifespan Management (Startup & Shutdown)
# ------------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manages application startup and shutdown events.

    On startup:
      1. Verifies/creates the PostgreSQL 'pgvector' extension.
      2. Creates database tables if they do not already exist.
      3. Verifies database connectivity.

    On shutdown:
      1. Disposes of the async database connection pool cleanly.
    """
    logger.info("Initializing %s in [%s] mode...", settings.PROJECT_NAME, settings.ENVIRONMENT)

    try:
        # Step A: Initialize pgvector extension
        await init_db_extensions()
        logger.info("PostgreSQL pgvector extension verified.")

        # Step B: Create database tables if missing
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database schema initialized successfully.")
    except Exception as exc:
        logger.warning(
            "Database initialization encountered an issue on startup: %s. "
            "Ensure PostgreSQL is running and DATABASE_URL is properly configured in .env.",
            str(exc),
        )

    yield  # Application is now receiving requests

    # Step C: Graceful shutdown
    logger.info("Shutting down %s and closing connection pools...", settings.PROJECT_NAME)
    await engine.dispose()
    logger.info("Database engine disposed cleanly.")


# ------------------------------------------------------------------------------
# 3. FastAPI Application Initialization
# ------------------------------------------------------------------------------
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=(
        "Production-ready AI Document Intelligence Assistant API with RAG, "
        "pgvector semantic search, Google Gemini embeddings, and multi-tenant JWT security."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)


# ------------------------------------------------------------------------------
# 4. CORS (Cross-Origin Resource Sharing) Middleware
# ------------------------------------------------------------------------------
cors_origins = list(settings.CORS_ORIGINS) if isinstance(settings.CORS_ORIGINS, list) else [settings.CORS_ORIGINS]
if "https://lidu12.github.io" not in cors_origins:
    cors_origins.append("https://lidu12.github.io")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_origin_regex=r"^https?://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ------------------------------------------------------------------------------
# 5. Global Exception Handlers
# ------------------------------------------------------------------------------
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Catches all domain-specific application exceptions and formats a standard JSON response."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status_code": exc.status_code,
            "error_type": exc.__class__.__name__,
            "detail": exc.detail,
        },
        headers=exc.headers,
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Formats Pydantic request body and query validation errors into readable structures."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY,
            "error_type": "ValidationError",
            "detail": "Request parameters or payload failed validation.",
            "errors": exc.errors(),
        },
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catches unhandled internal exceptions to prevent leakage of sensitive stack traces."""
    logger.exception("Unhandled server exception during request %s %s: %s", request.method, request.url.path, str(exc))
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "error_type": "InternalServerError",
            "detail": "An unexpected internal server error occurred." if settings.is_production else str(exc),
        },
    )


# ------------------------------------------------------------------------------
# 6. REST API Router Mounting
# ------------------------------------------------------------------------------
app.include_router(
    auth_router,
    prefix=f"{settings.API_V1_STR}/auth",
    tags=["Authentication"],
)

app.include_router(
    documents_router,
    prefix=f"{settings.API_V1_STR}/documents",
    tags=["Documents"],
)

app.include_router(
    chat_router,
    prefix=f"{settings.API_V1_STR}/chat",
    tags=["Chat & RAG"],
)


# ------------------------------------------------------------------------------
# 7. Root & Health Check Endpoints
# ------------------------------------------------------------------------------
@app.get(
    "/",
    tags=["General"],
    summary="Root API Status",
)
async def root() -> dict:
    """Returns basic service information and navigation links."""
    return {
        "service": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT,
        "docs_url": "/docs",
        "health_check": f"{settings.API_V1_STR}/health",
        "api_v1_prefix": settings.API_V1_STR,
    }


@app.get(
    "/health",
    tags=["General"],
    summary="Application Health Check",
)
@app.get(
    f"{settings.API_V1_STR}/health",
    tags=["General"],
    summary="Application & Database Health Check",
)
async def health_check() -> dict:
    """Performs an active database ping to confirm operational health."""
    db_status = "healthy"
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1;"))
    except Exception as exc:
        logger.warning("Health check failed database ping: %s", str(exc))
        db_status = f"unhealthy: {str(exc)}"

    return {
        "status": "ok" if db_status == "healthy" else "degraded",
        "database": db_status,
        "environment": settings.ENVIRONMENT,
    }
