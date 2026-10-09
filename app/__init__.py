"""AI Document Intelligence Assistant — Backend Application Package

A production-grade Document Intelligence & RAG system built with FastAPI,
PostgreSQL (pgvector), SQLAlchemy 2.0 (async), and Google Gemini AI.
"""

from app.main import app

__version__ = "1.0.0"
__author__ = "AI Document Intelligence Team"

__all__ = [
    "app",
    "__version__",
    "__author__",
]
