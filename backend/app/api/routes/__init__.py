"""API Routes Package

Exports route handlers for authentication, document management, and chat/RAG operations.
"""

from app.api.routes.auth import router as auth_router
from app.api.routes.chat import router as chat_router
from app.api.routes.documents import router as documents_router

__all__ = [
    "auth_router",
    "documents_router",
    "chat_router",
]
