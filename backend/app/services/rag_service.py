"""RAG (Retrieval-Augmented Generation) Orchestrator Service

Coordinates query embedding, vector similarity retrieval, LLM response generation,
structured citation mapping, and conversation persistence in PostgreSQL.
"""

import logging
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import ConversationNotFoundException
from app.models.chat import Conversation, Message
from app.schemas.chat import ChatQueryRequest, ChatResponse, CitationSource
from app.services.ai_service import ai_service
from app.services.embedding_service import embedding_service
from app.services.vector_service import RetrievedChunk, vector_service

logger = logging.getLogger(__name__)


class RAGService:
    """Orchestrates end-to-end RAG workflows."""

    async def answer_query(
        self,
        db: AsyncSession,
        user_id: int,
        request: ChatQueryRequest,
    ) -> ChatResponse:
        """Executes the complete grounded RAG pipeline for a user question.

        Args:
            db: Active async database session.
            user_id: ID of the authenticated user.
            request: ChatQueryRequest with message, conversation_id, and filters.

        Returns:
            ChatResponse: Grounded answer with structured citation sources.
        """
        # 1. Retrieve or create the conversation thread
        conversation = await self._get_or_create_conversation(
            db, user_id, request.conversation_id, request.message
        )

        # 2. Record the incoming user message in the database
        user_message = Message(
            conversation_id=conversation.id,
            role="user",
            content=request.message,
            sources=None,
        )
        db.add(user_message)
        await db.flush()  # Flush to assign user_message.id without committing

        # 3. Generate query vector embedding using Gemini API
        query_embedding = embedding_service.get_query_embedding(request.message)

        # 4. Search PostgreSQL for the most relevant document chunks
        top_k = request.top_k or settings.VECTOR_SEARCH_TOP_K
        retrieved_chunks: List[RetrievedChunk] = await vector_service.search_similar_chunks(
            db=db,
            user_id=user_id,
            query_embedding=query_embedding,
            top_k=top_k,
            similarity_threshold=settings.SIMILARITY_THRESHOLD,
            document_ids=request.document_ids,
        )

        # 5. Generate grounded response from Gemini
        if not retrieved_chunks:
            answer = (
                "I could not find any relevant information in your uploaded documents "
                "to answer this question. Please ensure relevant documents are uploaded and processed."
            )
            citations: List[CitationSource] = []
        else:
            answer = await ai_service.generate_grounded_answer(
                query=request.message,
                retrieved_chunks=retrieved_chunks,
            )

            # Map retrieved chunks to structured citations for the frontend
            citations = [
                CitationSource(
                    chunk_id=chunk.chunk_id,
                    document_id=chunk.document_id,
                    document_name=chunk.document_name,
                    page_number=chunk.page_number,
                    similarity_score=chunk.similarity_score,
                    snippet=chunk.content[:300] + "..." if len(chunk.content) > 300 else chunk.content,
                )
                for chunk in retrieved_chunks
            ]

        # 6. Save the AI's response and source citations to the database
        citations_payload = [c.model_dump() for c in citations] if citations else None
        assistant_message = Message(
            conversation_id=conversation.id,
            role="assistant",
            content=answer,
            sources=citations_payload,
        )
        db.add(assistant_message)
        await db.commit()
        await db.refresh(assistant_message)

        return ChatResponse(
            conversation_id=conversation.id,
            message_id=assistant_message.id,
            answer=answer,
            sources=citations,
            created_at=assistant_message.created_at,
        )

    @staticmethod
    async def _get_or_create_conversation(
        db: AsyncSession,
        user_id: int,
        conversation_id: Optional[int],
        initial_prompt: str,
    ) -> Conversation:
        """Finds an existing conversation or creates a new one with a descriptive title."""
        if conversation_id:
            query = select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id,
            )
            result = await db.execute(query)
            conversation = result.scalar_one_or_none()
            if not conversation:
                raise ConversationNotFoundException()
            return conversation

        # Auto-generate a title from the first 40 characters of the question
        title = initial_prompt.strip()[:40]
        if len(initial_prompt.strip()) > 40:
            title += "..."

        conversation = Conversation(
            user_id=user_id,
            title=title or "New Conversation",
        )
        db.add(conversation)
        await db.flush()
        return conversation


# Singleton instance
rag_service = RAGService()
