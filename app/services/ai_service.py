"""AI Generative Service (Google Gemini)

Handles generative text generation with strict grounding instructions,
temperature control for factual accuracy, and anti-hallucination guardrails.
"""

import logging
from typing import Dict, List, Optional
import google.generativeai as genai
from google.generativeai.types import GenerationConfig

from app.core.config import settings
from app.core.exceptions import AIServiceException
from app.services.vector_service import RetrievedChunk

logger = logging.getLogger(__name__)

SYSTEM_INSTRUCTION = """You are an expert, precise AI Document Intelligence Assistant.

Your primary duty is to answer the user's questions based EXCLUSIVELY on the provided document excerpts.

Strict Rules:
1. Grounding: Answer ONLY using the facts present in the [Context] section below.
2. Citations: When making a factual claim, cite the source using the format [Source N] where N matches the source number in the context.
3. Insufficient Information: If the provided [Context] does not contain enough information to answer the question accurately, explicitly state: "Based on the provided documents, I do not have enough information to answer this question." Do NOT make up or extrapolate facts.
4. Tone: Be professional, concise, objective, and clear.
"""


class AIService:
    """Service for generating grounded answers using Google Gemini."""

    def __init__(self) -> None:
        if settings.GEMINI_API_KEY:
            genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model_name = settings.GENERATIVE_MODEL

    async def generate_grounded_answer(
        self,
        query: str,
        retrieved_chunks: List[RetrievedChunk],
        chat_history: Optional[List[Dict[str, str]]] = None,
    ) -> str:
        """Generates an answer grounded strictly in the retrieved document chunks.

        Args:
            query: The user's question.
            retrieved_chunks: List of relevant document chunks retrieved by vector search.
            chat_history: Optional recent conversation messages for conversational context.

        Returns:
            str: Grounded AI response text.

        Raises:
            AIServiceException: If Gemini API fails.
        """
        if not settings.GEMINI_API_KEY:
            raise AIServiceException("Gemini API key is not configured in environment variables.")

        try:
            # 1. Format the context block with clear source numbers
            context_text = self._build_context_prompt(retrieved_chunks)

            # 2. Build the final prompt
            prompt_parts = [
                f"[Context]\n{context_text}\n\n",
                f"[User Question]\n{query}\n\n",
                "Provide a clear, grounded answer citing [Source N] tags where appropriate:",
            ]
            full_prompt = "".join(prompt_parts)

            # 3. Configure Gemini model with low temperature for factual precision
            model = genai.GenerativeModel(
                model_name=self.model_name,
                system_instruction=SYSTEM_INSTRUCTION,
                generation_config=GenerationConfig(
                    temperature=0.2,  # Low temperature prevents creativity/hallucination
                    top_p=0.95,
                    max_output_tokens=2048,
                ),
            )

            # 4. Generate response asynchronously
            response = await model.generate_content_async(full_prompt)
            return response.text.strip()

        except Exception as exc:
            logger.error(f"Gemini generation error: {exc}")
            raise AIServiceException(f"Failed to generate answer from AI model: {str(exc)}") from exc

    @staticmethod
    def _build_context_prompt(chunks: List[RetrievedChunk]) -> str:
        """Formats retrieved chunks into numbered source blocks for the prompt."""
        if not chunks:
            return "No relevant document excerpts found."

        formatted_sources: List[str] = []
        for index, chunk in enumerate(chunks, start=1):
            source_header = f"--- [Source {index}] (Document: {chunk.document_name}, Page: {chunk.page_number}) ---"
            formatted_sources.append(f"{source_header}\n{chunk.content}\n")

        return "\n".join(formatted_sources)


# Singleton instance
ai_service = AIService()
