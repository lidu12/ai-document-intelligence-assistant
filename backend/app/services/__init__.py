"""Services Package

Exports all application business logic services for document parsing,
chunking, embedding generation, vector search, RAG orchestration, and authentication.
"""

from app.services.ai_service import AIService, ai_service
from app.services.auth_service import AuthService, auth_service
from app.services.chunking_service import ChunkingService, RawChunk
from app.services.document_parser import (
    DocumentParser,
    ParsedDocument,
    ParsedPage,
)
from app.services.document_service import DocumentService, document_service
from app.services.embedding_service import EmbeddingService, embedding_service
from app.services.rag_service import RAGService, rag_service
from app.services.vector_service import (
    RetrievedChunk,
    VectorService,
    vector_service,
)

__all__ = [
    # Parser & Chunking
    "DocumentParser",
    "ParsedDocument",
    "ParsedPage",
    "ChunkingService",
    "RawChunk",
    # Embeddings & Vector Search
    "EmbeddingService",
    "embedding_service",
    "VectorService",
    "vector_service",
    "RetrievedChunk",
    # AI & RAG
    "AIService",
    "ai_service",
    "RAGService",
    "rag_service",
    # Business Management
    "DocumentService",
    "document_service",
    "AuthService",
    "auth_service",
]
