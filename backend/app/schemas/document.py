"""Document & DocumentChunk Pydantic Schemas

Validates and serializes document upload responses, metadata, status tracking,
and detailed chunk data with page numbers.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class DocumentChunkResponse(BaseModel):
    """Schema representing an individual text chunk of a document."""

    id: int
    document_id: int
    chunk_index: int = Field(..., description="Zero-based index of chunk in document")
    content: str = Field(..., description="Text content of the chunk")
    page_number: int = Field(..., description="Page number where chunk was found")
    char_count: int = Field(..., description="Character count of chunk")
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentResponse(BaseModel):
    """Schema for document summary and status information."""

    id: int
    user_id: int
    filename: str
    file_type: str
    file_size_bytes: int
    total_pages: int
    total_chunks: int
    status: str = Field(..., description="'pending', 'processing', 'ready', 'failed'")
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentDetailResponse(DocumentResponse):
    """Detailed schema including the document metadata and all its parsed chunks."""

    chunks: List[DocumentChunkResponse] = []


class DocumentListResponse(BaseModel):
    """Schema for returning a paginated list of user documents."""

    documents: List[DocumentResponse]
    total_count: int


class DocumentUploadResponse(BaseModel):
    """Initial response returned immediately when a file is uploaded."""

    id: int
    filename: str
    status: str
    message: str = "Document uploaded successfully and queued for processing"
