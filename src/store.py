from __future__ import annotations

from typing import Any, Callable

from .chunking import _dot
from .embeddings import _mock_embed
from .models import Document


class EmbeddingStore:
    """
    A vector store for text chunks.

    Uses an in-memory store for this lab.
    """

    def __init__(
        self,
        collection_name: str = "documents",
        embedding_fn: Callable[[str], list[float]] | None = None,
    ) -> None:
        self._embedding_fn = embedding_fn or _mock_embed
        self._collection_name = collection_name

        # CP4: chỉ dùng in-memory, không dùng ChromaDB
        self._use_chroma = False
        self._store: list[dict[str, Any]] = []
        self._collection = None
        self._next_index = 0

    def _make_record(self, doc: Document) -> dict[str, Any]:
        """Build a normalized stored record for one document."""

        metadata = dict(doc.metadata or {})

        # doc_id trong metadata phải tồn tại để delete_document()
        # có thể tìm tất cả chunk thuộc cùng document.
        metadata.setdefault("doc_id", doc.id)

        embedding = self._embedding_fn(doc.content)

        return {
            "id": doc.id,
            "content": doc.content,
            "metadata": metadata,
            "embedding": embedding,
        }

    def _search_records(
        self,
        query: str,
        records: list[dict[str, Any]],
        top_k: int,
    ) -> list[dict[str, Any]]:
        """Run similarity search over the provided records."""

        if not records or top_k <= 0:
            return []

        query_embedding = self._embedding_fn(query)

        scored = []

        for record in records:
            score = _dot(query_embedding, record["embedding"])

            result = {
                "id": record["id"],
                "content": record["content"],
                "metadata": dict(record["metadata"]),
                "score": score,
            }

            scored.append(result)

        scored.sort(key=lambda x: x["score"], reverse=True)

        return scored[:top_k]

    def add_documents(self, docs: list[Document]) -> None:
        """
        Embed each document's content and store it.
        """

        for doc in docs:
            record = self._make_record(doc)
            self._store.append(record)

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """
        Find the top_k most similar documents to query.
        """

        return self._search_records(
            query=query,
            records=self._store,
            top_k=top_k,
        )

    def get_collection_size(self) -> int:
        """Return the total number of stored chunks."""

        return len(self._store)

    def search_with_filter(
        self,
        query: str,
        top_k: int = 3,
        metadata_filter: dict = None,
    ) -> list[dict]:
        """
        Search with optional metadata pre-filtering.

        First filter stored chunks by metadata_filter,
        then run similarity search.
        """

        # Không có filter → search toàn bộ
        if not metadata_filter:
            return self._search_records(
                query=query,
                records=self._store,
                top_k=top_k,
            )

        # Filter TRƯỚC khi similarity search
        filtered_records = []

        for record in self._store:
            metadata = record.get("metadata", {})

            matches = all(
                metadata.get(key) == value
                for key, value in metadata_filter.items()
            )

            if matches:
                filtered_records.append(record)

        return self._search_records(
            query=query,
            records=filtered_records,
            top_k=top_k,
        )

    def add_documents_with_embeddings(
        self,
        docs: list[Document],
        embeddings: list[list[float]],
    ):
        if len(docs) != len(embeddings):
            raise ValueError(
                "Number of documents and embeddings must match"
            )

        for doc, embedding in zip(docs, embeddings):
            metadata = dict(doc.metadata or {})
            metadata.setdefault("doc_id", doc.id)

            self._store.append(
                {
                    "id": doc.id,
                    "content": doc.content,
                    "metadata": metadata,
                    "embedding": embedding,
                }
            )

    def delete_document(self, doc_id: str) -> bool:
        """
        Remove all chunks belonging to a document.

        Returns True if any chunks were removed, False otherwise.
        """

        original_size = len(self._store)

        self._store = [
            record
            for record in self._store
            if record.get("metadata", {}).get("doc_id") != doc_id
        ]

        return len(self._store) < original_size