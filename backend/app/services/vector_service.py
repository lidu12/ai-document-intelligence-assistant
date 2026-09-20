"""Vector Similarity Search Service

Executes multi-tenant semantic vector similarity searches in PostgreSQL using
the pgvector cosine distance operator (<=>), strictly isolated by user ID.
"""

from dataclasses import dataclass
import logging
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.document import Document, DocumentChunk

logger = logging.getLogger(__name__)


@dataclass
class RetrievedChunk:
    """Represents a document chunk retrieved from a vector similarity search."""

    chunk_id: int
    document_id: int
    document_name: str
    page_number: int
    content: str
    similarity_score: float


class VectorService:
    """Performs scoped pgvector similarity queries on document embeddings."""

    @staticmethod
    async def search_similar_chunks(
        db: AsyncSession,
        user_id: int,
        query_embedding: List[float],
        top_k: int = settings.VECTOR_SEARCH_TOP_K,
        similarity_threshold: float = settings.SIMILARITY_THRESHOLD,
        document_ids: Optional[List[int]] = None,
    ) -> List[RetrievedChunk]:
        """Searches for the most semantically relevant chunks belonging to a specific user.

        Args:
            db: Active async SQLAlchemy database session.
            user_id: ID of the user performing the search (tenant isolation).
            query_embedding: 768-dimensional float vector of the user's question.
            top_k: Maximum number of chunks to return.
            similarity_threshold: Minimum cosine similarity score (0.0 to 1.0) required.
            document_ids: Optional list of document IDs to restrict the search to.

        Returns:
            List[RetrievedChunk]: Ranked list of relevant chunks above the threshold.
        """
        # Cosine distance in pgvector: 0 = identical, 2 = opposite.
        # Cosine similarity = 1 - cosine_distance.
        cosine_dist = DocumentChunk.embedding.cosine_distance(query_embedding)
        similarity = (1.0 - cosine_dist).label("similarity_score")

        # Build query joining DocumentChunk to Document for strict user isolation
        query = (
            select(
                DocumentChunk.id.label("chunk_id"),
                Document.id.label("document_id"),
                Document.filename.label("document_name"),
                DocumentChunk.page_number,
                DocumentChunk.content,
                similarity,
            )
            .join(Document, DocumentChunk.document_id == Document.id)
            .where(Document.user_id == user_id)
            .where(Document.status == "ready")
            .where(DocumentChunk.embedding.is_not(None))
        )

        # Optional filter for specific documents
        if document_ids:
            query = query.where(Document.id.in_(document_ids))

        # Order by closest distance (smallest cosine distance / highest similarity)
        query = query.order_by(cosine_dist.asc()).limit(top_k)

        result = await db.execute(query)
        rows = result.all()

        retrieved: List[RetrievedChunk] = []
        for row in rows:
            sim_score = float(row.similarity_score)
            # Filter out chunks that do not meet the minimum similarity threshold
            if sim_score >= similarity_threshold:
                retrieved.append(
                    RetrievedChunk(
                        chunk_id=row.chunk_id,
                        document_id=row.document_id,
                        document_name=row.document_name,
                        page_number=row.page_number,
                        content=row.content,
                        similarity_score=round(sim_score, 4),
                    )
                )

        return retrieved


# Singleton instance
vector_service = VectorService()
