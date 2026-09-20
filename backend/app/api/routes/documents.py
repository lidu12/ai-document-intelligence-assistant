"""Document Management API Router

Provides HTTP REST endpoints for uploading, listing, viewing, and deleting
user documents and text chunks with strict tenant isolation.
"""

from fastapi import (
    APIRouter,
    Depends,
    File,
    Query,
    UploadFile,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_db
from app.models.user import User
from app.schemas.document import (
    DocumentDetailResponse,
    DocumentListResponse,
    DocumentResponse,
)
from app.services.document_service import document_service

router = APIRouter()


@router.post(
    "/upload",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and ingest a document (PDF or TXT)",
)
async def upload_document(
    file: UploadFile = File(..., description="PDF or TXT file to upload"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> DocumentResponse:
    """Uploads a file, extracts text, generates vector embeddings, and stores chunks."""
    file_bytes = await file.read()
    filename = file.filename or "uploaded_document"
    content_type = file.content_type

    doc = await document_service.process_and_save_document(
        db=db,
        user_id=current_user.id,
        file_bytes=file_bytes,
        filename=filename,
        content_type=content_type,
    )
    return doc


@router.get(
    "",
    response_model=DocumentListResponse,
    summary="List all documents uploaded by the current user",
)
async def list_documents(
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> DocumentListResponse:
    """Returns a paginated list of all documents belonging to the authenticated user."""
    documents, total = await document_service.get_user_documents(
        db=db,
        user_id=current_user.id,
        skip=skip,
        limit=limit,
    )
    return DocumentListResponse(documents=documents, total_count=total)


@router.get(
    "/{document_id}",
    response_model=DocumentDetailResponse,
    summary="Get document details and extracted chunks",
)
async def get_document(
    document_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> DocumentDetailResponse:
    """Retrieves document metadata along with its parsed chunks and page numbers."""
    doc = await document_service.get_user_document_by_id(
        db=db,
        user_id=current_user.id,
        document_id=document_id,
    )
    return doc


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a document and its vector embeddings",
)
async def delete_document(
    document_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Deletes a document and automatically purges all related chunks from the database."""
    await document_service.delete_user_document(
        db=db,
        user_id=current_user.id,
        document_id=document_id,
    )
