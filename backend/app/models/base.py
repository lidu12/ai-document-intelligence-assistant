"""SQLAlchemy Declarative Base & Reusable Mixins

Provides the root Base class and common mixins (timestamps, automatic table naming)
using modern SQLAlchemy 2.0 type-annotated mapped columns.
"""

from datetime import datetime, timezone
import re
from sqlalchemy import DateTime, func
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    declared_attr,
    mapped_column,
)


def utc_now() -> datetime:
    """Returns current UTC timestamp with timezone information."""
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    """Root Declarative Base class for all SQLAlchemy ORM models."""

    # Automatically generate __tablename__ in snake_case from the class name.
    # E.g., class DocumentChunk -> table name: 'document_chunks'
    @declared_attr.directive
    def __tablename__(cls) -> str:
        name = cls.__name__
        # Convert PascalCase to snake_case (e.g., DocumentChunk -> document_chunk)
        snake_name = re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()
        # Pluralize simple table names if not already ending in 's'
        if not snake_name.endswith("s"):
            snake_name += "s"
        return snake_name


class TimestampMixin:
    """Reusable mixin providing created_at and updated_at timestamp columns.

    Uses PostgreSQL server-side default functions for precision and consistency.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        server_default=func.now(),
        nullable=False,
        doc="Timestamp when the record was initially created (UTC)",
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        server_default=func.now(),
        onupdate=utc_now,
        server_onupdate=func.now(),
        nullable=False,
        doc="Timestamp when the record was last modified (UTC)",
    )
