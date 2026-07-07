"""
Memory & retrieval layer — Build #026–#028.

Real SQLite-backed episodic + semantic memory, with optional ChromaDB vector
store. Falls back to a pure-Python cosine-similarity index if ChromaDB isn't
installed, so tests pass in any environment.

Public API:
    MemoryStore        - key/value + episodic events (SQLite)
    VectorStore        - semantic search (ChromaDB or pure-Python fallback)
    RetrievalEngine    - unified search across both
    Memory             - convenience facade combining all three
"""

from monad.memory.store import Memory, MemoryStore, EpisodicEvent
from monad.memory.vector import VectorStore
from monad.memory.retrieval import RetrievalEngine, RetrievalResult

__all__ = [
    "Memory", "MemoryStore", "EpisodicEvent",
    "VectorStore", "RetrievalEngine", "RetrievalResult",
]
