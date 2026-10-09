"""User Database Model

Defines the User entity representing registered accounts, credential storage,
authorization flags, and relationships to user-owned documents and conversations.
"""

from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

# TYPE_CHECKING prevents circular import errors when importing related models for type hints
if TYPE_CHECKING:
    from app.models.document import Document
    from app.models.chat import Conversation


class User(Base, TimestampMixin):
    """Represents a registered user in the database."""

    # --------------------------------------------------------------------------
    # 1. Primary Key & Identity Columns
    # --------------------------------------------------------------------------
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        index=True,
        doc="Unique primary key identifier for the user",
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
        doc="Unique email address used for login and notifications",
    )

    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Cryptographically salted and hashed password (never plaintext)",
    )

    full_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        doc="Optional display name of the user",
    )

    # --------------------------------------------------------------------------
    # 2. Status & Permission Flags
    # --------------------------------------------------------------------------
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        doc="Whether the user account is active (can be disabled instead of deleted)",
    )

    is_superuser: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        doc="Grants administrator permissions across the system",
    )

    # --------------------------------------------------------------------------
    # 3. Relationships to User Data (One-to-Many with Cascading Deletion)
    # --------------------------------------------------------------------------
    # If a user is deleted, all their documents and vector chunks are automatically deleted.
    documents: Mapped[List["Document"]] = relationship(
        "Document",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    # If a user is deleted, all their conversation threads and messages are deleted.
    conversations: Mapped[List["Conversation"]] = relationship(
        "Conversation",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email='{self.email}' is_active={self.is_active}>"
