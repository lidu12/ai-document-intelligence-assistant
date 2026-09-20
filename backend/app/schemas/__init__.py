"""Pydantic Schemas Package

Exports all request and response schemas across authentication, documents,
and chat/RAG operations.
"""

from app.schemas.auth import (
    Token,
    TokenPayload,
    UserCreate,
    UserLogin,
    UserResponse,
    UserUpdate,
)
from app.schemas.chat import (
    ChatQueryRequest,
    ChatResponse,
    CitationSource,
    ConversationDetailResponse,
    ConversationListResponse,
    ConversationResponse,
    ConversationUpdate,
    MessageResponse,
)
from app.schemas.document import (
    DocumentChunkResponse,
    DocumentDetailResponse,
    DocumentListResponse,
    DocumentResponse,
    DocumentUploadResponse,
)

__all__ = [
    # Auth
    "UserCreate",
    "UserLogin",
    "UserUpdate",
    "UserResponse",
    "Token",
    "TokenPayload",
    # Document
    "DocumentChunkResponse",
    "DocumentResponse",
    "DocumentDetailResponse",
    "DocumentListResponse",
    "DocumentUploadResponse",
    # Chat & RAG
    "CitationSource",
    "ChatQueryRequest",
    "MessageResponse",
    "ChatResponse",
    "ConversationResponse",
    "ConversationDetailResponse",
    "ConversationListResponse",
    "ConversationUpdate",
]
