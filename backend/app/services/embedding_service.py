"""Embedding Service

Generates 768-dimensional vector embeddings for text chunks and search queries
using the Google Gemini Embedding API (text-embedding-004).
"""

import logging
from typing import List
import google.generativeai as genai

from app.core.config import settings
from app.core.exceptions import AIServiceException

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for computing vector representations of text using Gemini API."""

    def __init__(self) -> None:
        if settings.GEMINI_API_KEY:
            genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = settings.EMBEDDING_MODEL
        self.dimension = settings.EMBEDDING_DIMENSION

    def get_query_embedding(self, query_text: str) -> List[float]:
        """Generates a single embedding vector for a user's search query.

        Args:
            query_text: The user's question or search prompt.

        Returns:
            List[float]: 768-dimensional float vector.

        Raises:
            AIServiceException: If the Gemini API request fails.
        """
        if not settings.GEMINI_API_KEY:
            raise AIServiceException("Gemini API key is not configured in environment variables.")

        try:
            cleaned_query = query_text.strip()
            if not cleaned_query:
                raise AIServiceException("Query text cannot be empty for embedding generation.")

            response = genai.embed_content(
                model=self.model,
                content=cleaned_query,
                task_type="RETRIEVAL_QUERY",
            )
            embedding = response["embedding"]
            return embedding

        except Exception as exc:
            logger.error(f"Failed to generate query embedding: {exc}")
            raise AIServiceException(f"Embedding generation failed: {str(exc)}") from exc

    def get_document_embeddings_batch(
        self,
        texts: List[str],
        batch_size: int = 50,
    ) -> List[List[float]]:
        """Generates embeddings for a batch of document text chunks.

        Args:
            texts: List of text strings to embed.
            batch_size: Number of chunks per API batch call (default 50).

        Returns:
            List[List[float]]: Ordered list of 768-dimensional vector embeddings.

        Raises:
            AIServiceException: If any batch embedding request fails.
        """
        if not texts:
            return []

        if not settings.GEMINI_API_KEY:
            raise AIServiceException("Gemini API key is not configured in environment variables.")

        all_embeddings: List[List[float]] = []

        try:
            for i in range(0, len(texts), batch_size):
                batch = texts[i : i + batch_size]
                response = genai.embed_content(
                    model=self.model,
                    content=batch,
                    task_type="RETRIEVAL_DOCUMENT",
                )
                embeddings = response["embedding"]

                # Ensure single embedding is wrapped if only one text in batch
                if isinstance(embeddings[0], float):
                    all_embeddings.append(embeddings)
                else:
                    all_embeddings.extend(embeddings)

            return all_embeddings

        except Exception as exc:
            logger.error(f"Failed to generate batch document embeddings: {exc}")
            raise AIServiceException(f"Batch embedding generation failed: {str(exc)}") from exc


# Singleton instance for application-wide dependency injection
embedding_service = EmbeddingService()
