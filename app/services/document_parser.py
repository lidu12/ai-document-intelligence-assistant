"""Document Parser Service

Extracts structured text and page numbers from uploaded PDF and TXT files
using in-memory streaming without creating temporary disk files.
"""

from dataclasses import dataclass
import io
from typing import List, Optional
import pypdf

from app.core.config import settings
from app.core.exceptions import (
    DocumentProcessingException,
    InvalidFileTypeException,
)


@dataclass
class ParsedPage:
    """Represents text extracted from a single page of a document."""

    page_number: int
    text: str
    char_count: int


@dataclass
class ParsedDocument:
    """Represents the complete parsed content and metadata of a document."""

    filename: str
    file_type: str
    pages: List[ParsedPage]
    total_pages: int
    total_chars: int


class DocumentParser:
    """In-memory parser for extracting text content from supported file types."""

    @classmethod
    def parse(
        cls,
        file_bytes: bytes,
        filename: str,
        content_type: Optional[str] = None,
    ) -> ParsedDocument:
        """Parses in-memory file bytes into structured pages based on file extension.

        Args:
            file_bytes: Raw binary content of the uploaded file.
            filename: Original name of the uploaded file.
            content_type: Optional MIME type provided by the HTTP client.

        Returns:
            ParsedDocument: Structured text organized by page number.

        Raises:
            InvalidFileTypeException: If the file extension is not supported.
            DocumentProcessingException: If parsing fails due to corruption or encryption.
        """
        extension = filename.split(".")[-1].lower() if "." in filename else ""

        if extension not in settings.ALLOWED_FILE_EXTENSIONS:
            raise InvalidFileTypeException(settings.ALLOWED_FILE_EXTENSIONS)

        if extension == "pdf":
            return cls._parse_pdf(file_bytes, filename)
        elif extension == "txt":
            return cls._parse_txt(file_bytes, filename)
        else:
            raise InvalidFileTypeException(settings.ALLOWED_FILE_EXTENSIONS)

    @classmethod
    def _parse_pdf(cls, file_bytes: bytes, filename: str) -> ParsedDocument:
        """Extracts text page-by-page from PDF binary data using pypdf."""
        try:
            stream = io.BytesIO(file_bytes)
            reader = pypdf.PdfReader(stream)

            if reader.is_encrypted:
                try:
                    # Attempt empty password decrypt for soft-locked PDFs
                    reader.decrypt("")
                except Exception:
                    raise DocumentProcessingException(
                        f"PDF '{filename}' is password protected and cannot be processed."
                    )

            pages: List[ParsedPage] = []
            total_chars = 0

            for index, page in enumerate(reader.pages):
                raw_text = page.extract_text() or ""
                cleaned_text = cls._clean_text(raw_text)

                # Skip completely blank pages to save chunking and embedding costs
                if not cleaned_text.strip():
                    continue

                page_char_count = len(cleaned_text)
                total_chars += page_char_count

                pages.append(
                    ParsedPage(
                        page_number=index + 1,  # 1-indexed for human readability
                        text=cleaned_text,
                        char_count=page_char_count,
                    )
                )

            if not pages:
                raise DocumentProcessingException(
                    f"PDF '{filename}' contains no extractable text. It may be scanned images."
                )

            return ParsedDocument(
                filename=filename,
                file_type="application/pdf",
                pages=pages,
                total_pages=len(reader.pages),
                total_chars=total_chars,
            )

        except DocumentProcessingException:
            raise
        except Exception as exc:
            raise DocumentProcessingException(
                f"Failed to read PDF '{filename}': {str(exc)}"
            ) from exc

    @classmethod
    def _parse_txt(cls, file_bytes: bytes, filename: str) -> ParsedDocument:
        """Extracts text from plain text files with automatic encoding detection."""
        # Try UTF-8 first, fallback to Latin-1
        text = ""
        for encoding in ("utf-8", "utf-8-sig", "latin-1"):
            try:
                text = file_bytes.decode(encoding)
                break
            except UnicodeDecodeError:
                continue

        if not text:
            raise DocumentProcessingException(
                f"Unable to decode text file '{filename}'. Ensure it is UTF-8 encoded."
            )

        cleaned_text = cls._clean_text(text)
        if not cleaned_text.strip():
            raise DocumentProcessingException(f"Text file '{filename}' is empty.")

        page = ParsedPage(
            page_number=1,
            text=cleaned_text,
            char_count=len(cleaned_text),
        )

        return ParsedDocument(
            filename=filename,
            file_type="text/plain",
            pages=[page],
            total_pages=1,
            total_chars=len(cleaned_text),
        )

    @staticmethod
    def _clean_text(text: str) -> str:
        """Removes null bytes and normalizes line breaks and whitespace."""
        text = text.replace("\x00", "")  # Remove null bytes which break PostgreSQL text fields
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        return text
