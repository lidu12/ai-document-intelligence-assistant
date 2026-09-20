"""Document Ingestion & Management Test Suite

Automated tests for uploading TXT/PDF files, file validation,
pagination, chunk inspection, multi-tenant isolation, and cascade deletion.
"""

import io
import pytest
from httpx import AsyncClient

from app.models.user import User


# Helper: generates a minimal valid single-page PDF byte stream for testing
def create_sample_pdf_bytes() -> bytes:
    """Generates a minimal valid PDF file byte stream in memory."""
    return (
        b"%PDF-1.4\n"
        b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
        b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Resources<<>>>>endobj\n"
        b"xref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n0000000052 00000 n\n0000000101 00000 n\n"
        b"trailer<</Size 4/Root 1 0 R>>\nstartxref\n178\n%%EOF\n"
    )


# ------------------------------------------------------------------------------
# 1. Document Upload & Ingestion Tests
# ------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_upload_txt_document_success(client: AsyncClient, auth_headers: dict):
    """Tests uploading a plain text document, extracting text, and generating chunks."""
    content = (
        "Artificial Intelligence and Machine Learning are transforming modern software engineering. "
        "Retrieval-Augmented Generation (RAG) allows LLMs to retrieve relevant knowledge from external "
        "documents before generating accurate, factual responses."
    )
    files = {
        "file": ("ai_overview.txt", io.BytesIO(content.encode("utf-8")), "text/plain"),
    }

    response = await client.post("/api/v1/documents/upload", headers=auth_headers, files=files)
    assert response.status_code == 201

    data = response.json()
    assert data["filename"] == "ai_overview.txt"
    assert data["status"] == "ready"
    assert data["total_chunks"] >= 1
    assert data["total_pages"] == 1
    assert data["file_size_bytes"] > 0
    assert "id" in data


@pytest.mark.asyncio
async def test_upload_pdf_document_success(client: AsyncClient, auth_headers: dict):
    """Tests uploading a valid PDF document and storing document metadata."""
    pdf_bytes = create_sample_pdf_bytes()
    files = {
        "file": ("sample_report.pdf", io.BytesIO(pdf_bytes), "application/pdf"),
    }

    response = await client.post("/api/v1/documents/upload", headers=auth_headers, files=files)
    assert response.status_code == 201

    data = response.json()
    assert data["filename"] == "sample_report.pdf"
    assert data["status"] == "ready"
    assert data["file_type"] == "application/pdf"


@pytest.mark.asyncio
async def test_upload_invalid_file_type_fails(client: AsyncClient, auth_headers: dict):
    """Verifies that unsupported file extensions (.exe, .jpg) are rejected with 400 Bad Request."""
    files = {
        "file": ("malicious_script.exe", io.BytesIO(b"executable binary data"), "application/octet-stream"),
    }
    response = await client.post("/api/v1/documents/upload", headers=auth_headers, files=files)
    assert response.status_code == 400
    assert "unsupported file type" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_upload_oversized_file_fails(client: AsyncClient, auth_headers: dict):
    """Verifies that files exceeding the configured MAX_UPLOAD_SIZE_MB are rejected with 413."""
    # Create 11 MB of dummy data (limit is configured at 10 MB)
    oversized_data = b"X" * (11 * 1024 * 1024)
    files = {
        "file": ("giant_file.txt", io.BytesIO(oversized_data), "text/plain"),
    }
    response = await client.post("/api/v1/documents/upload", headers=auth_headers, files=files)
    assert response.status_code == 413
    assert "exceeds the maximum limit" in response.json()["detail"].lower()


# ------------------------------------------------------------------------------
# 2. Document Listing & Pagination Tests
# ------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_list_user_documents(client: AsyncClient, auth_headers: dict):
    """Verifies that a user can list all their uploaded documents with pagination."""
    # Upload two test documents
    for i in range(2):
        files = {
            "file": (f"doc_{i}.txt", io.BytesIO(f"Content for doc {i}".encode("utf-8")), "text/plain"),
        }
        await client.post("/api/v1/documents/upload", headers=auth_headers, files=files)

    response = await client.get("/api/v1/documents?skip=0&limit=10", headers=auth_headers)
    assert response.status_code == 200

    data = response.json()
    assert "documents" in data
    assert "total_count" in data
    assert data["total_count"] >= 2
    assert len(data["documents"]) >= 2


# ------------------------------------------------------------------------------
# 3. Document Details & Chunk Inspection Tests
# ------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_get_document_details_with_chunks(client: AsyncClient, auth_headers: dict):
    """Verifies retrieving a single document and inspecting its extracted chunks."""
    content = "Detailed engineering document text for chunk inspection testing."
    files = {
        "file": ("inspect_me.txt", io.BytesIO(content.encode("utf-8")), "text/plain"),
    }
    upload_res = await client.post("/api/v1/documents/upload", headers=auth_headers, files=files)
    doc_id = upload_res.json()["id"]

    response = await client.get(f"/api/v1/documents/{doc_id}", headers=auth_headers)
    assert response.status_code == 200

    data = response.json()
    assert data["id"] == doc_id
    assert "chunks" in data
    assert len(data["chunks"]) >= 1
    assert data["chunks"][0]["content"] == content
    assert data["chunks"][0]["page_number"] == 1


# ------------------------------------------------------------------------------
# 4. Multi-Tenant Authorization & Isolation Tests
# ------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_multi_tenant_document_isolation(
    client: AsyncClient,
    auth_headers: dict,
    second_auth_headers: dict,
):
    """CRITICAL SECURITY TEST: Verifies User B cannot view or delete User A's documents."""
    # User A uploads a private document
    files = {
        "file": ("user_a_confidential.txt", io.BytesIO(b"Confidential financial data"), "text/plain"),
    }
    upload_res = await client.post("/api/v1/documents/upload", headers=auth_headers, files=files)
    doc_a_id = upload_res.json()["id"]

    # User B attempts to read User A's document
    get_res = await client.get(f"/api/v1/documents/{doc_a_id}", headers=second_auth_headers)
    assert get_res.status_code == 404
    assert "not found or access denied" in get_res.json()["detail"].lower()

    # User B attempts to delete User A's document
    del_res = await client.delete(f"/api/v1/documents/{doc_a_id}", headers=second_auth_headers)
    assert del_res.status_code == 404

    # User A can still view their own document safely
    owner_res = await client.get(f"/api/v1/documents/{doc_a_id}", headers=auth_headers)
    assert owner_res.status_code == 200


# ------------------------------------------------------------------------------
# 5. Document Deletion & Cascade Tests
# ------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_delete_document_success(client: AsyncClient, auth_headers: dict):
    """Verifies that deleting a document returns 204 No Content and purges it from DB."""
    files = {
        "file": ("delete_me.txt", io.BytesIO(b"Data to be deleted"), "text/plain"),
    }
    upload_res = await client.post("/api/v1/documents/upload", headers=auth_headers, files=files)
    doc_id = upload_res.json()["id"]

    # Delete the document
    del_res = await client.delete(f"/api/v1/documents/{doc_id}", headers=auth_headers)
    assert del_res.status_code == 204

    # Confirm it is no longer retrievable
    get_res = await client.get(f"/api/v1/documents/{doc_id}", headers=auth_headers)
    assert get_res.status_code == 404
