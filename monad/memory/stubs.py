"""
STUB implementations for the memory layer.

These allow the rest of Monad to reference the memory API today, and be replaced
by real SQLite + ChromaDB implementations in Builds #026–#035.
"""

from __future__ import annotations

from typing import Any


class MemoryStore:
    """STUB: eventually SQLite-backed key/value + episodic memory."""

    def __init__(self) -> None:
        self._kv: dict[str, Any] = {}

    def put(self, key: str, value: Any) -> None:
        self._kv[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        return self._kv.get(key, default)

    def all(self) -> dict[str, Any]:
        return dict(self._kv)


class VectorStore:
    """STUB: eventually ChromaDB-backed vector index."""

    def __init__(self) -> None:
        self._docs: list[tuple[str, str]] = []  # (id, text)

    def add(self, doc_id: str, text: str, embedding: list[float] | None = None) -> None:
        self._docs.append((doc_id, text))

    def query(self, text: str, top_k: int = 5) -> list[tuple[str, float]]:
        # Naive substring match until real vector search is wired
        results = [(d, 1.0) for d, t in self._docs if text.lower() in t.lower()]
        return results[:top_k]


class RetrievalEngine:
    """STUB: combines MemoryStore + VectorStore into a single retrieval API."""

    def __init__(self, memory: MemoryStore, vectors: VectorStore) -> None:
        self.memory = memory
        self.vectors = vectors

    def retrieve(self, query: str, top_k: int = 5) -> list[str]:
        hits = self.vectors.query(query, top_k=top_k)
        return [doc_id for doc_id, _ in hits]
