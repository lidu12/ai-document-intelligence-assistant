"""Application Configuration Module

Centralized, type-safe application settings managed via Pydantic v2 BaseSettings.
Reads environment variables and .env files, validating all types and constraints on boot.
"""

from functools import lru_cache
from typing import List, Union
from pydantic import (
    field_validator,
    ValidationInfo,
)
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Core application settings and environment variable definitions."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",  # Ignore any extra environment variables not defined here
    )

    # --------------------------------------------------------------------------
    # 1. Project & Environment
    # --------------------------------------------------------------------------
    PROJECT_NAME: str = "AI Document Intelligence Assistant"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"

    # --------------------------------------------------------------------------
    # 2. Database (PostgreSQL with pgvector)
    # --------------------------------------------------------------------------
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/doc_intelligence"
    DATABASE_ECHO_SQL: bool = False

    # --------------------------------------------------------------------------
    # 3. Security & JWT
    # --------------------------------------------------------------------------
    SECRET_KEY: str = "replace-with-a-secure-random-secret-key-at-least-32-chars-long"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    # --------------------------------------------------------------------------
    # 4. Google Gemini AI & Embeddings
    # --------------------------------------------------------------------------
    GEMINI_API_KEY: str = ""
    EMBEDDING_MODEL: str = "models/gemini-embedding-001"
    EMBEDDING_DIMENSION: int = 768
    GENERATIVE_MODEL: str = "models/gemini-3.6-flash"

    # --------------------------------------------------------------------------
    # 5. Document Ingestion & Chunking
    # --------------------------------------------------------------------------
    MAX_UPLOAD_SIZE_MB: int = 10
    ALLOWED_FILE_EXTENSIONS: List[str] = ["pdf", "txt"]
    CHUNK_SIZE_CHARS: int = 1500
    CHUNK_OVERLAP_CHARS: int = 200

    # --------------------------------------------------------------------------
    # 6. RAG Retrieval & Similarity Search
    # --------------------------------------------------------------------------
    VECTOR_SEARCH_TOP_K: int = 5
    SIMILARITY_THRESHOLD: float = 0.35

    # --------------------------------------------------------------------------
    # 7. CORS Origins
    # --------------------------------------------------------------------------
    CORS_ORIGINS: Union[List[str], str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]], info: ValidationInfo) -> List[str]:
        """Ensures CORS_ORIGINS is always parsed into a list of strings,

        even if provided as a comma-separated string in .env.
        """
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        return v

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_database_url(cls, v: str, info: ValidationInfo) -> str:
        """Normalizes cloud PostgreSQL connection strings (e.g. Supabase, Render, Neon)
        to use the asynchronous asyncpg driver scheme.
        """
        if isinstance(v, str):
            # Standardize postgresql:// or postgres:// to postgresql+asyncpg://
            if v.startswith("postgres://"):
                v = v.replace("postgres://", "postgresql+asyncpg://", 1)
            elif v.startswith("postgresql://") and not v.startswith("postgresql+asyncpg://"):
                v = v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v

    @property
    def max_upload_size_bytes(self) -> int:
        """Helper property: calculates the maximum upload size in bytes."""
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    @property
    def is_production(self) -> bool:
        """Helper property: checks if application is running in production mode."""
        return self.ENVIRONMENT.lower() == "production"


@lru_cache()
def get_settings() -> Settings:
    """Creates and caches a singleton instance of the application Settings.

    Using lru_cache ensures the settings file is read only once during app startup.
    """
    return Settings()


# Global settings instance for easy imports across the application
settings: Settings = get_settings()
