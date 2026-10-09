"""Database Models Package

Exposes all SQLAlchemy ORM models in a single namespace to simplify imports
and ensure all table definitions are registered with Base.metadata for migrations
and table creation.
"""

from app.models.base import Base, TimestampMixin, utc_now
from app.models.chat import Conversation, Message
from app.models.document import Document, DocumentChunk
from app.models.user import User

__all__ = [
    "Base",
    "TimestampMixin",
    "utc_now",
    "User",
    "Document",
    "DocumentChunk",
    "Conversation",
    "Message",
]
