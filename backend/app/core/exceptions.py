"""Custom Application Exceptions

Standardized, domain-specific HTTP exceptions for authentication, file handling,
multi-tenant authorization, and AI service errors.
"""

from typing import Any, Dict, Optional
from fastapi import HTTPException, status


class AppException(HTTPException):
    """Base exception for all application-specific errors."""

    def __init__(
        self,
        status_code: int,
        detail: str,
        headers: Optional[Dict[str, str]] = None,
    ) -> None:
        super().__init__(status_code=status_code, detail=detail, headers=headers)


# ------------------------------------------------------------------------------
# 1. Authentication & Authorization Exceptions
# ------------------------------------------------------------------------------
class InvalidCredentialsException(AppException):
    """Raised when user provides incorrect email or password during login."""

    def __init__(self, detail: str = "Incorrect email or password") -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class UnauthorizedException(AppException):
    """Raised when an invalid, missing, or expired JWT token is provided."""

    def __init__(self, detail: str = "Could not validate credentials") -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class ForbiddenException(AppException):
    """Raised when an authenticated user attempts to access an unauthorized resource."""

    def __init__(self, detail: str = "Operation not permitted") -> None:
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
        )


class InactiveUserException(AppException):
    """Raised when an account exists but is marked as inactive/disabled."""

    def __init__(self, detail: str = "User account is inactive") -> None:
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
        )


class UserAlreadyExistsException(AppException):
    """Raised when registering an account with an email that is already in use."""

    def __init__(self, detail: str = "A user with this email already exists") -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
        )


# ------------------------------------------------------------------------------
# 2. Resource Not Found Exceptions
# ------------------------------------------------------------------------------
class NotFoundException(AppException):
    """Raised when a generic requested resource cannot be found."""

    def __init__(self, detail: str = "Resource not found") -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
        )


class DocumentNotFoundException(NotFoundException):
    """Raised when a document ID does not exist or does not belong to the user."""

    def __init__(self, detail: str = "Document not found or access denied") -> None:
        super().__init__(detail=detail)


class ConversationNotFoundException(NotFoundException):
    """Raised when a conversation ID does not exist or does not belong to the user."""

    def __init__(self, detail: str = "Conversation not found or access denied") -> None:
        super().__init__(detail=detail)


# ------------------------------------------------------------------------------
# 3. File Ingestion & Validation Exceptions
# ------------------------------------------------------------------------------
class FileValidationException(AppException):
    """Raised when an uploaded file fails integrity or format checks."""

    def __init__(self, detail: str = "Uploaded file failed validation") -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
        )


class FileTooLargeException(AppException):
    """Raised when an uploaded file exceeds the configured maximum byte size."""

    def __init__(self, max_mb: int) -> None:
        super().__init__(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds the maximum limit of {max_mb} MB",
        )


class InvalidFileTypeException(AppException):
    """Raised when an uploaded file extension/MIME type is not supported."""

    def __init__(self, allowed_types: list[str]) -> None:
        formatted = ", ".join(f".{ext}" for ext in allowed_types)
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type. Allowed formats: {formatted}",
        )


class DocumentProcessingException(AppException):
    """Raised when text extraction or parsing from a document fails."""

    def __init__(self, detail: str = "Failed to parse and extract text from document") -> None:
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
        )


# ------------------------------------------------------------------------------
# 4. External AI & Embedding Exceptions
# ------------------------------------------------------------------------------
class AIServiceException(AppException):
    """Raised when external LLM or embedding provider (Google Gemini) fails."""

    def __init__(self, detail: str = "AI service temporarily unavailable") -> None:
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail,
        )
