"""Conversation & Message Database Models

Defines the Conversation entity (chat sessions owned by a user) and the
Message entity (user prompts and AI responses with grounded source citations).
"""

from typing import TYPE_CHECKING, Any, Dict, List, Optional
from sqlalchemy import ForeignKey, Integer, String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User


class Conversation(Base, TimestampMixin):
    """Represents a multi-turn chat session between a user and the AI assistant."""

    # --------------------------------------------------------------------------
    # 1. Primary Key & User Ownership
    # --------------------------------------------------------------------------
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        index=True,
        doc="Unique primary key identifier for the conversation session",
    )

    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="ID of the user who owns this conversation session",
    )

    # --------------------------------------------------------------------------
    # 2. Conversation Metadata
    # --------------------------------------------------------------------------
    title: Mapped[str] = mapped_column(
        String(255),
        default="New Conversation",
        nullable=False,
        doc="Human-readable title for the chat session, e.g., 'Q3 Financial Review'",
    )

    # --------------------------------------------------------------------------
    # 3. Relationships
    # --------------------------------------------------------------------------
    # Links back to the owner User
    user: Mapped["User"] = relationship(
        "User",
        back_populates="conversations",
    )

    # One conversation contains many messages ordered chronologically.
    # When a conversation is deleted, all its messages are automatically deleted (cascade).
    messages: Mapped[List["Message"]] = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="Message.created_at",
    )

    def __repr__(self) -> str:
        return f"<Conversation id={self.id} user_id={self.user_id} title='{self.title}'>"


class Message(Base, TimestampMixin):
    """Represents an individual message (user inquiry or AI response with citations)."""

    # --------------------------------------------------------------------------
    # 1. Primary Key & Conversation Association
    # --------------------------------------------------------------------------
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        index=True,
        doc="Unique primary key identifier for the message",
    )

    conversation_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="ID of the parent conversation this message belongs to",
    )

    # --------------------------------------------------------------------------
    # 2. Message Content & Role
    # --------------------------------------------------------------------------
    role: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        doc="Role of the message sender: 'user', 'assistant', or 'system'",
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Full textual body of the user prompt or LLM generated response",
    )

    # --------------------------------------------------------------------------
    # 3. RAG Grounding & Citations (JSON Payload)
    # --------------------------------------------------------------------------
    # Stores structured citations for assistant answers:
    # [
    #   {
    #     "chunk_id": 42,
    #     "document_id": 3,
    #     "document_name": "quarterly_report.pdf",
    #     "page_number": 4,
    #     "similarity_score": 0.89,
    #     "snippet": "Revenue grew by 14% year-over-year..."
    #   }
    # ]
    sources: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(
        JSON,
        nullable=True,
        doc="Structured list of retrieved document chunks used as ground truth for this answer",
    )

    # --------------------------------------------------------------------------
    # 4. Relationships
    # --------------------------------------------------------------------------
    conversation: Mapped["Conversation"] = relationship(
        "Conversation",
        back_populates="messages",
    )

    def __repr__(self) -> str:
        return f"<Message id={self.id} conv_id={self.conversation_id} role='{self.role}'>"
