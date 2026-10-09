"""Document Ingestion & Management Service

Orchestrates file upload validation, text extraction, chunking, embedding generation,
and atomic database persistence with multi-tenant isolation.
"""

import logging
from typing import List, Optional, Tuple
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import (
    DocumentNotFoundException,
    FileTooLargeException,
    InvalidFileTypeException,
)
from app.models.document import Document, DocumentChunk
from app.services.chunking_service import ChunkingService
from app.services.document_parser import DocumentParser
from app.services.embedding_service import embedding_service

logger = logging.getLogger(__name__)


class DocumentService:
    """Manages document lifecycle from upload and embedding to deletion."""

    def __init__(self) -> None:
        self.chunker = ChunkingService()

    async def process_and_save_document(
        self,
        db: AsyncSession,
        user_id: int,
        file_bytes: bytes,
        filename: str,
        content_type: Optional[str] = None,
    ) -> Document:
        """Validates, parses, chunks, embeds, and saves an uploaded document.

        Args:
            db: Active async database session.
            user_id: ID of the uploading user.
            file_bytes: Raw binary content of the file.
            filename: Original file name.
            content_type: Optional MIME type.

        Returns:
            Document: Saved and populated Document record.
        """
        # 1. Validate file size
        file_size = len(file_bytes)
        if file_size > settings.max_upload_size_bytes:
            raise FileTooLargeException(settings.MAX_UPLOAD_SIZE_MB)

        # 2. Validate file extension
        ext = filename.split(".")[-1].lower() if "." in filename else ""
        if ext not in settings.ALLOWED_FILE_EXTENSIONS:
            raise InvalidFileTypeException(settings.ALLOWED_FILE_EXTENSIONS)

        # 3. Create initial Document entry with status 'processing'
        doc = Document(
            user_id=user_id,
            filename=filename,
            file_type=content_type or f"application/{ext}",
            file_size_bytes=file_size,
            status="processing",
            total_pages=1,
            total_chunks=0,
        )
        db.add(doc)
        await db.flush()

        try:
            # 4. Extract text page-by-page
            parsed_doc = DocumentParser.parse(file_bytes, filename, content_type)
            doc.total_pages = parsed_doc.total_pages

            # 5. Split document into semantic chunks with overlap
            raw_chunks = self.chunker.chunk_document(parsed_doc)
            doc.total_chunks = len(raw_chunks)

            # 6. Generate batch vector embeddings using Gemini
            chunk_texts = [c.content for c in raw_chunks]
            embeddings = embedding_service.get_document_embeddings_batch(chunk_texts)

            # 7. Create DocumentChunk records with vectors
            for chunk_data, vector in zip(raw_chunks, embeddings):
                chunk_record = DocumentChunk(
                    document_id=doc.id,
                    chunk_index=chunk_data.chunk_index,
                    content=chunk_data.content,
                    page_number=chunk_data.page_number,
                    char_count=chunk_data.char_count,
                    embedding=vector,
                )
                db.add(chunk_record)

            # 8. Mark document as ready
            doc.status = "ready"
            await db.commit()
            await db.refresh(doc)
            return doc

        except Exception as exc:
            logger.error(f"Document ingestion failed for '{filename}': {exc}")
            await db.rollback()
            # Update status to failed so the user sees clear feedback
            doc.status = "failed"
            doc.error_message = str(exc)
            db.add(doc)
            await db.commit()
            await db.refresh(doc)
            raise

    async def get_user_documents(
        self,
        db: AsyncSession,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[List[Document], int]:
        """Retrieves paginated documents owned by the specified user."""
        count_query = select(func.count(Document.id)).where(Document.user_id == user_id)
        total_count = (await db.execute(count_query)).scalar_one()

        docs_query = (
            select(Document)
            .where(Document.user_id == user_id)
            .order_by(Document.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(docs_query)
        documents = list(result.scalars().all())

        return documents, total_count

    async def get_user_document_by_id(
        self,
        db: AsyncSession,
        user_id: int,
        document_id: int,
    ) -> Document:
        """Retrieves a single document owned by the user, or raises 404."""
        query = select(Document).where(
            Document.id == document_id,
            Document.user_id == user_id,
        )
        result = await db.execute(query)
        document = result.scalar_one_or_none()

        if not document:
            raise DocumentNotFoundException()
        return document

    async def delete_user_document(
        self,
        db: AsyncSession,
        user_id: int,
        document_id: int,
    ) -> None:
        """Deletes a user's document and cascades deletion of its vector chunks."""
        document = await self.get_user_document_by_id(db, user_id, document_id)
        await db.delete(document)
        await db.commit()


# Singleton instance
document_service = DocumentService()
