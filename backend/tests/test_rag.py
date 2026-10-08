"""RAG (Retrieval-Augmented Generation) & Chat Test Suite

Automated tests for semantic vector retrieval, grounded answer generation,
source citations, multi-turn conversation memory, and conversation thread management.
"""

import io
from unittest.mock import AsyncMock, patch
import pytest
from httpx import AsyncClient

from app.models.user import User
from app.services.vector_service import RetrievedChunk


# Helper: Uploads a test document for RAG query testing
async def upload_test_doc(client: AsyncClient, auth_headers: dict) -> int:
    content = (
        "FastAPI is a modern, high-performance web framework for building APIs with Python. "
        "Retrieval-Augmented Generation (RAG) is an AI framework that retrieves facts from an "
        "external knowledge base to ground large language models (LLMs) on accurate information."
    )
    files = {
        "file": ("rag_guide.txt", io.BytesIO(content.encode("utf-8")), "text/plain"),
    }
    res = await client.post("/api/v1/documents/upload", headers=auth_headers, files=files)
    return res.json()["id"]


# ------------------------------------------------------------------------------
# 1. Core RAG Pipeline & Citation Tests
# ------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_chat_query_creates_conversation_and_citations(client: AsyncClient, auth_headers: dict):
    """Tests executing a RAG query, creating a conversation, and returning citations."""
    doc_id = await upload_test_doc(client, auth_headers)

    mock_retrieved_chunks = [
        RetrievedChunk(
            chunk_id=1,
            document_id=doc_id,
            document_name="rag_guide.txt",
            page_number=1,
            content="Retrieval-Augmented Generation (RAG) retrieves facts from external knowledge.",
            similarity_score=0.88,
        )
    ]

    with patch(
        "app.services.rag_service.vector_service.search_similar_chunks",
        new_callable=AsyncMock,
        return_value=mock_retrieved_chunks,
    ):
        payload = {
            "query": "What is RAG?",
        }
        response = await client.post("/api/v1/chat", headers=auth_headers, json=payload)
        assert response.status_code == 200

        data = response.json()
        assert "answer" in data
        assert "conversation_id" in data
        assert data["conversation_id"] > 0
        assert "sources" in data
        assert len(data["sources"]) == 1
        assert data["sources"][0]["document_id"] == doc_id
        assert data["sources"][0]["document_name"] == "rag_guide.txt"
        assert data["sources"][0]["page_number"] == 1
        assert data["sources"][0]["similarity_score"] == 0.88


@pytest.mark.asyncio
async def test_chat_query_multi_turn_conversation(client: AsyncClient, auth_headers: dict):
    """Tests asking a follow-up question inside an existing conversation thread."""
    doc_id = await upload_test_doc(client, auth_headers)

    mock_retrieved_chunks = [
        RetrievedChunk(
            chunk_id=1,
            document_id=doc_id,
            document_name="rag_guide.txt",
            page_number=1,
            content="FastAPI is a modern web framework.",
            similarity_score=0.85,
        )
    ]

    with patch(
        "app.services.rag_service.vector_service.search_similar_chunks",
        new_callable=AsyncMock,
        return_value=mock_retrieved_chunks,
    ):
        # Turn 1: Initial Question
        res_1 = await client.post("/api/v1/chat", headers=auth_headers, json={"query": "What is FastAPI?"})
        assert res_1.status_code == 200
        conv_id = res_1.json()["conversation_id"]

        # Turn 2: Follow-up Question inside same conversation
        res_2 = await client.post(
            "/api/v1/chat",
            headers=auth_headers,
            json={"query": "Is it fast?", "conversation_id": conv_id},
        )
        assert res_2.status_code == 200
        assert res_2.json()["conversation_id"] == conv_id

        # Verify conversation contains 4 total messages (2 user + 2 assistant)
        conv_res = await client.get(f"/api/v1/chat/conversations/{conv_id}", headers=auth_headers)
        assert conv_res.status_code == 200
        conv_data = conv_res.json()
        assert len(conv_data["messages"]) == 4


@pytest.mark.asyncio
async def test_chat_query_no_relevant_chunks_fallback(client: AsyncClient, auth_headers: dict):
    """Verifies safe fallback message when no relevant chunks exceed similarity threshold."""
    with patch(
        "app.services.rag_service.vector_service.search_similar_chunks",
        new_callable=AsyncMock,
        return_value=[],
    ):
        payload = {"query": "Tell me something unrelated to any document"}
        response = await client.post("/api/v1/chat", headers=auth_headers, json=payload)
        assert response.status_code == 200

        data = response.json()
        assert "not find any relevant information" in data["answer"].lower()
        assert len(data["sources"]) == 0


# ------------------------------------------------------------------------------
# 2. Conversation Management Tests (List, Get, Patch, Delete)
# ------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_conversation_management_lifecycle(client: AsyncClient, auth_headers: dict):
    """Verifies listing, retrieving, renaming, and deleting conversations."""
    # Create a conversation by querying
    res = await client.post("/api/v1/chat", headers=auth_headers, json={"query": "Test query"})
    conv_id = res.json()["conversation_id"]

    # 1. List conversations
    list_res = await client.get("/api/v1/chat/conversations", headers=auth_headers)
    assert list_res.status_code == 200
    assert list_res.json()["total_count"] >= 1

    # 2. Rename conversation title
    patch_res = await client.patch(
        f"/api/v1/chat/conversations/{conv_id}",
        headers=auth_headers,
        json={"title": "Updated Custom Title"},
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["title"] == "Updated Custom Title"

    # 3. Delete conversation
    del_res = await client.delete(f"/api/v1/chat/conversations/{conv_id}", headers=auth_headers)
    assert del_res.status_code == 204

    # 4. Confirm deleted
    get_res = await client.get(f"/api/v1/chat/conversations/{conv_id}", headers=auth_headers)
    assert get_res.status_code == 404


# ------------------------------------------------------------------------------
# 3. Multi-Tenant Conversation Security Tests
# ------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_multi_tenant_conversation_isolation(
    client: AsyncClient,
    auth_headers: dict,
    second_auth_headers: dict,
):
    """CRITICAL SECURITY TEST: Verifies User B cannot access User A's conversations."""
    # User A creates a conversation
    res = await client.post("/api/v1/chat", headers=auth_headers, json={"query": "User A secret inquiry"})
    conv_id = res.json()["conversation_id"]

    # User B attempts to read User A's conversation
    get_res = await client.get(f"/api/v1/chat/conversations/{conv_id}", headers=second_auth_headers)
    assert get_res.status_code == 404
    assert "not found or access denied" in get_res.json()["detail"].lower()

    # User B attempts to delete User A's conversation
    del_res = await client.delete(f"/api/v1/chat/conversations/{conv_id}", headers=second_auth_headers)
    assert del_res.status_code == 404
