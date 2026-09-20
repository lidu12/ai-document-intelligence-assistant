"""Text Chunking Service

Splits extracted document text into semantic chunks with sliding-window overlap
while preserving page number attribution for accurate citations.
"""

from dataclasses import dataclass
from typing import List

from app.core.config import settings
from app.services.document_parser import ParsedDocument, ParsedPage


@dataclass
class RawChunk:
    """Represents an extracted text chunk with positional and page metadata."""

    chunk_index: int
    content: str
    page_number: int
    char_count: int


class ChunkingService:
    """Splits document pages into semantically bounded text chunks."""

    def __init__(
        self,
        chunk_size: int = settings.CHUNK_SIZE_CHARS,
        chunk_overlap: int = settings.CHUNK_OVERLAP_CHARS,
    ) -> None:
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        # Ensure overlap is always strictly less than chunk size
        if self.chunk_overlap >= self.chunk_size:
            self.chunk_overlap = self.chunk_size // 5

    def chunk_document(self, parsed_doc: ParsedDocument) -> List[RawChunk]:
        """Processes all pages of a parsed document into a sequential list of chunks.

        Args:
            parsed_doc: ParsedDocument containing page-by-page text.

        Returns:
            List[RawChunk]: Ordered chunks ready for vector embedding.
        """
        all_chunks: List[RawChunk] = []
        global_chunk_index = 0

        for page in parsed_doc.pages:
            page_text_chunks = self._chunk_page_text(page.text)

            for chunk_text in page_text_chunks:
                cleaned = chunk_text.strip()
                if not cleaned:
                    continue

                all_chunks.append(
                    RawChunk(
                        chunk_index=global_chunk_index,
                        content=cleaned,
                        page_number=page.page_number,
                        char_count=len(cleaned),
                    )
                )
                global_chunk_index += 1

        return all_chunks

    def _chunk_page_text(self, text: str) -> List[str]:
        """Splits a single page of text using a recursive character splitting strategy."""
        if len(text) <= self.chunk_size:
            return [text]

        chunks: List[str] = []
        # Separators ordered from largest semantic block to smallest
        separators = ["\n\n", "\n", ". ", "? ", "! ", "; ", " ", ""]

        chunks = self._recursive_split(text, separators, self.chunk_size, self.chunk_overlap)
        return chunks

    def _recursive_split(
        self,
        text: str,
        separators: List[str],
        chunk_size: int,
        chunk_overlap: int,
    ) -> List[str]:
        """Recursively breaks text using the highest-level natural separator available."""
        final_chunks: List[str] = []

        if len(text) <= chunk_size or not separators:
            if text.strip():
                final_chunks.append(text)
            return final_chunks

        # Pick the best current separator
        separator = separators[0]
        remaining_separators = separators[1:]

        if separator == "":
            # Hard character split fallback
            splits = [text[i : i + chunk_size] for i in range(0, len(text), chunk_size - chunk_overlap)]
            return [s for s in splits if s.strip()]

        parts = text.split(separator)
        current_chunk: List[str] = []
        current_length = 0

        for part in parts:
            part_len = len(part) + len(separator)

            if current_length + part_len <= chunk_size:
                current_chunk.append(part)
                current_length += part_len
            else:
                if current_chunk:
                    joined = separator.join(current_chunk)
                    final_chunks.append(joined)
                    # Create overlap by keeping end parts
                    overlap_parts: List[str] = []
                    overlap_len = 0
                    for p in reversed(current_chunk):
                        if overlap_len + len(p) + len(separator) <= chunk_overlap:
                            overlap_parts.insert(0, p)
                            overlap_len += len(p) + len(separator)
                        else:
                            break
                    current_chunk = overlap_parts
                    current_length = overlap_len

                # If a single part exceeds chunk size, split it with remaining separators
                if len(part) > chunk_size:
                    sub_chunks = self._recursive_split(
                        part, remaining_separators, chunk_size, chunk_overlap
                    )
                    final_chunks.extend(sub_chunks)
                else:
                    current_chunk.append(part)
                    current_length += len(part) + len(separator)

        if current_chunk:
            joined = separator.join(current_chunk)
            if joined.strip():
                final_chunks.append(joined)

        return final_chunks
