"""Chat & RAG Pydantic Schemas

Defines schemas for chat queries, grounded AI responses with citation sources,
and conversation history.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class CitationSource(BaseModel):
    """Represents a specific document chunk citation supporting an AI answer."""

    chunk_id: int = Field(..., description="ID of the retrieved text chunk")
    document_id: int = Field(..., description="ID of the parent document")
    document_name: str = Field(..., description="Name of the source file (e.g. report.pdf)")
    page_number: int = Field(..., description="Page number where the evidence is located")
    similarity_score: float = Field(..., description="Cosine similarity score (0.0 to 1.0)")
    snippet: str = Field(..., description="Exact excerpt from the source chunk")


class ChatQueryRequest(BaseModel):
    """Incoming user question payload for the RAG assistant."""

    message: Optional[str] = Field(
        None,
        min_length=1,
        max_length=4000,
        description="The question or prompt to ask about documents",
    )
    query: Optional[str] = Field(
        None,
        min_length=1,
        max_length=4000,
        description="Alias for message",
    )
    conversation_id: Optional[int] = Field(
        None,
        description="Optional existing conversation ID. If None, a new conversation is created.",
    )
    document_id: Optional[int] = Field(
        None,
        description="Optional single document ID to search within.",
    )
    document_ids: Optional[List[int]] = Field(
        None,
        description="Optional list of specific document IDs to search within. If None, searches all user documents.",
    )
    top_k: Optional[int] = Field(
        None,
        ge=1,
        le=20,
        description="Optional custom number of relevant chunks to retrieve",
    )

    @property
    def query_text(self) -> str:
        """Returns either query or message as the sanitized prompt text."""
        text = self.query or self.message
        if not text or not text.strip():
            raise ValueError("Either 'query' or 'message' must be provided.")
        return text.strip()

    @property
    def target_document_ids(self) -> Optional[List[int]]:
        """Consolidates document_id and document_ids into a single list."""
        if self.document_ids:
            return self.document_ids
        if self.document_id is not None:
            return [self.document_id]
        return None


class MessageResponse(BaseModel):
    """Schema for a single message in a conversation thread."""

    id: int
    conversation_id: int
    role: str = Field(..., description="'user', 'assistant', or 'system'")
    content: str
    sources: Optional[List[CitationSource]] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChatResponse(BaseModel):
    """Response returned after running the RAG pipeline."""

    conversation_id: int
    message_id: int
    answer: str
    sources: List[CitationSource] = []
    created_at: datetime


class ConversationResponse(BaseModel):
    """Summary of a chat conversation thread."""

    id: int
    user_id: int
    title: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConversationDetailResponse(ConversationResponse):
    """Full conversation including its ordered message history."""

    messages: List[MessageResponse] = []


class ConversationListResponse(BaseModel):
    """Paginated list of user conversations."""

    conversations: List[ConversationResponse]
    total_count: int


class ConversationUpdate(BaseModel):
    """Schema for renaming a conversation title."""

    title: str = Field(..., min_length=1, max_length=255)
