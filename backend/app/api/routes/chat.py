"""Chat & RAG API Router

Provides HTTP REST endpoints for asking grounded questions about documents,
managing conversations, and retrieving historical chat messages with source citations.
"""

from fastapi import (
    APIRouter,
    Depends,
    Query,
    status,
)
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_active_user, get_db
from app.core.exceptions import ConversationNotFoundException
from app.models.chat import Conversation
from app.models.user import User
from app.schemas.chat import (
    ChatQueryRequest,
    ChatResponse,
    ConversationDetailResponse,
    ConversationListResponse,
    ConversationResponse,
    ConversationUpdate,
)
from app.services.rag_service import rag_service

router = APIRouter()


@router.post(
    "",
    response_model=ChatResponse,
    summary="Ask a question about uploaded documents (RAG)",
)
async def query_assistant(
    request: ChatQueryRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ChatResponse:
    """Executes the RAG pipeline: retrieves relevant chunks, generates grounded answer, and returns citations."""
    return await rag_service.answer_query(
        db=db,
        user_id=current_user.id,
        request=request,
    )


@router.get(
    "/conversations",
    response_model=ConversationListResponse,
    summary="List all conversations for the current user",
)
async def list_conversations(
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ConversationListResponse:
    """Returns a paginated list of chat conversation sessions owned by the user."""
    count_query = select(func.count(Conversation.id)).where(Conversation.user_id == current_user.id)
    total = (await db.execute(count_query)).scalar_one()

    convs_query = (
        select(Conversation)
        .where(Conversation.user_id == current_user.id)
        .order_by(Conversation.updated_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(convs_query)
    conversations = list(result.scalars().all())

    return ConversationListResponse(conversations=conversations, total_count=total)


@router.get(
    "/conversations/{conversation_id}",
    response_model=ConversationDetailResponse,
    summary="Get conversation details and full message history",
)
async def get_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ConversationDetailResponse:
    """Retrieves a single conversation thread along with its ordered messages and source citations."""
    query = (
        select(Conversation)
        .options(selectinload(Conversation.messages))
        .where(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id,
        )
    )
    result = await db.execute(query)
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise ConversationNotFoundException()

    return conversation


@router.patch(
    "/conversations/{conversation_id}",
    response_model=ConversationResponse,
    summary="Update conversation title",
)
async def update_conversation(
    conversation_id: int,
    update_data: ConversationUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ConversationResponse:
    """Renames an existing conversation title."""
    query = select(Conversation).where(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id,
    )
    result = await db.execute(query)
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise ConversationNotFoundException()

    conversation.title = update_data.title
    await db.commit()
    await db.refresh(conversation)
    return conversation


@router.delete(
    "/conversations/{conversation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a conversation and all its messages",
)
async def delete_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Deletes a conversation session and cascades deletion to all messages in the thread."""
    query = select(Conversation).where(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id,
    )
    result = await db.execute(query)
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise ConversationNotFoundException()

    await db.delete(conversation)
    await db.commit()
