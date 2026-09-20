"""Document & DocumentChunk Database Models

Defines the Document entity (metadata, processing status) and the
DocumentChunk entity (text content, page numbers, pgvector embeddings).
"""

from typing import TYPE_CHECKING, List, Optional
from pgvector.sqlalchemy import Vector
from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.config import settings
from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User


class Document(Base, TimestampMixin):
    """Represents an uploaded document (PDF, TXT) owned by a user."""

    # --------------------------------------------------------------------------
    # 1. Primary Key & Ownership
    # --------------------------------------------------------------------------
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        index=True,
        doc="Unique primary key for the document",
    )

    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="ID of the user who uploaded this document",
    )

    # --------------------------------------------------------------------------
    # 2. File Metadata
    # --------------------------------------------------------------------------
    filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Original name of the uploaded file (e.g., 'contract.pdf')",
    )

    file_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        doc="MIME type or file extension (e.g., 'application/pdf', 'text/plain')",
    )

    file_size_bytes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        doc="Size of the uploaded file in bytes",
    )

    total_pages: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
        doc="Total number of pages extracted from the document",
    )

    total_chunks: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        doc="Total number of text chunks generated for this document",
    )

    # --------------------------------------------------------------------------
    # 3. Ingestion & Processing Status
    # --------------------------------------------------------------------------
    status: Mapped[str] = mapped_column(
        String(50),
        default="pending",
        nullable=False,
        index=True,
        doc="Processing status: 'pending', 'processing', 'ready', 'failed'",
    )

    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Detailed error message if processing failed",
    )

    # --------------------------------------------------------------------------
    # 4. Relationships
    # --------------------------------------------------------------------------
    # Links back to the owner User
    user: Mapped["User"] = relationship(
        "User",
        back_populates="documents",
    )

    # One document contains many chunks. If the document is deleted, delete all its chunks.
    chunks: Mapped[List["DocumentChunk"]] = relationship(
        "DocumentChunk",
        back_populates="document",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="DocumentChunk.chunk_index",
    )

    def __repr__(self) -> str:
        return f"<Document id={self.id} filename='{self.filename}' status='{self.status}'>"


class DocumentChunk(Base, TimestampMixin):
    """Represents a single text chunk with its pgvector semantic embedding."""

    # --------------------------------------------------------------------------
    # 1. Primary Key & Document Association
    # --------------------------------------------------------------------------
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        index=True,
        doc="Unique primary key for the chunk",
    )

    document_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="ID of the parent document this chunk belongs to",
    )

    # --------------------------------------------------------------------------
    # 2. Chunk Content & Positional Metadata
    # --------------------------------------------------------------------------
    chunk_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        doc="Zero-based sequential order of the chunk inside the document",
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="The actual plain text content of this chunk",
    )

    page_number: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
        doc="The document page number where this chunk originated",
    )

    char_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        doc="Number of characters contained in this chunk",
    )

    # --------------------------------------------------------------------------
    # 3. Vector Embedding (pgvector)
    # --------------------------------------------------------------------------
    # Uses 768 dimensions to match Google Gemini text-embedding-004
    embedding: Mapped[Optional[List[float]]] = mapped_column(
        Vector(settings.EMBEDDING_DIMENSION),
        nullable=True,
        doc="768-dimensional float vector generated by Gemini embedding model",
    )

    # --------------------------------------------------------------------------
    # 4. Relationships
    # --------------------------------------------------------------------------
    document: Mapped["Document"] = relationship(
        "Document",
        back_populates="chunks",
    )

    def __repr__(self) -> str:
        return f"<DocumentChunk id={self.id} doc_id={self.document_id} index={self.chunk_index} page={self.page_number}>"
