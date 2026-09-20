from __future__ import annotations

import math
import re


class FixedSizeChunker:
    """
    Split text into fixed-size chunks with optional overlap.

    Rules:
        - Each chunk is at most chunk_size characters long.
        - Consecutive chunks share overlap characters.
        - The last chunk contains whatever remains.
        - If text is shorter than chunk_size, return [text].
    """

    def __init__(self, chunk_size: int = 500, overlap: int = 50) -> None:
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        if len(text) <= self.chunk_size:
            return [text]

        step = self.chunk_size - self.overlap
        chunks: list[str] = []
        for start in range(0, len(text), step):
            chunk = text[start : start + self.chunk_size]
            chunks.append(chunk)
            if start + self.chunk_size >= len(text):
                break
        return chunks


class SentenceChunker:
    """
    Split text into chunks of at most max_sentences_per_chunk sentences.

    Sentence detection: split on ". ", "! ", "? " or ".\n".
    Strip extra whitespace from each chunk.
    """

    def __init__(self, max_sentences_per_chunk: int = 3) -> None:
        self.max_sentences_per_chunk = max(1, max_sentences_per_chunk)

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []

        # Tách SAU dấu câu để giữ lại ., !, ?
        sentences = re.split(r"(?<=[.!?])(?:\s+|$)", text.strip())

        sentences = [s.strip() for s in sentences if s.strip()]

        chunks = []

        for i in range(0, len(sentences), self.max_sentences_per_chunk):
            chunk = " ".join(
                sentences[i : i + self.max_sentences_per_chunk]
            ).strip()

            if chunk:
                chunks.append(chunk)

        return chunks


class RecursiveChunker:
    """
    Recursively split text using separators in priority order.

    Default separator priority:
        ["\n\n", "\n", ". ", " ", ""]
    """

    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(
        self,
        separators: list[str] | None = None,
        chunk_size: int = 500,
    ) -> None:
        self.separators = (
            self.DEFAULT_SEPARATORS
            if separators is None
            else list(separators)
        )
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []

        chunks = self._split(text.strip(), self.separators)

        return [chunk.strip() for chunk in chunks if chunk.strip()]

    def _split(
        self,
        current_text: str,
        remaining_separators: list[str],
    ) -> list[str]:
        current_text = current_text.strip()

        if not current_text:
            return []

        # Base case
        if len(current_text) <= self.chunk_size:
            return [current_text]

        # Không còn separator -> hard split
        if not remaining_separators:
            return [
                current_text[i : i + self.chunk_size]
                for i in range(0, len(current_text), self.chunk_size)
            ]

        separator = remaining_separators[0]
        next_separators = remaining_separators[1:]

        # Separator rỗng -> hard split
        if separator == "":
            return [
                current_text[i : i + self.chunk_size]
                for i in range(0, len(current_text), self.chunk_size)
            ]

        # Không có separator hiện tại -> thử separator tiếp theo
        if separator not in current_text:
            return self._split(current_text, next_separators)

        pieces = current_text.split(separator)

        chunks: list[str] = []
        current_chunk = ""

        for piece in pieces:
            piece = piece.strip()

            if not piece:
                continue

            candidate = (
                piece
                if not current_chunk
                else current_chunk + separator + piece
            )

            if len(candidate) <= self.chunk_size:
                current_chunk = candidate
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())

                if len(piece) <= self.chunk_size:
                    current_chunk = piece
                else:
                    # Piece vẫn quá dài -> đệ quy separator nhỏ hơn
                    chunks.extend(
                        self._split(piece, next_separators)
                    )
                    current_chunk = ""

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def compute_similarity(
    vec_a: list[float],
    vec_b: list[float],
) -> float:
    """
    Compute cosine similarity between two vectors.

    cosine_similarity = dot(a, b) / (||a|| * ||b||)

    Returns 0.0 if either vector has zero magnitude.
    """

    norm_a = math.sqrt(_dot(vec_a, vec_a))
    norm_b = math.sqrt(_dot(vec_b, vec_b))

    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0

    return _dot(vec_a, vec_b) / (norm_a * norm_b)


class ChunkingStrategyComparator:
    """Run all built-in chunking strategies and compare their results."""

    def compare(self, text: str, chunk_size: int = 200) -> dict:
        fixed = FixedSizeChunker(
            chunk_size=chunk_size,
            overlap=0,
        ).chunk(text)

        sentence = SentenceChunker(
            max_sentences_per_chunk=3
        ).chunk(text)

        recursive = RecursiveChunker(
            chunk_size=chunk_size
        ).chunk(text)

        def stats(chunks: list[str]) -> dict:
            count = len(chunks)

            if count == 0:
                avg_length = 0.0
            else:
                avg_length = sum(len(chunk) for chunk in chunks) / count

            return {
                "count": count,
                "avg_length": avg_length,
                "chunks": chunks,
            }

        return {
            "fixed_size": stats(fixed),
            "by_sentences": stats(sentence),
            "recursive": stats(recursive),
        }