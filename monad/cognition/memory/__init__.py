"""
Memory layer — Cognee integration with graceful fallback.

Cognee (https://github.com/topoteretes/cognee) is optional. When absent, we
fall back to a lightweight in-process memory that stores triplets and does
simple substring / keyword retrieval so the rest of Monad still works.

Also exposes QueryRouter (Phase 6): routes queries to graph_only / vector_only
/ hybrid / temporal / feeling_lucky based on heuristic patterns.
"""

from monad.cognition.memory.store import MemoryLayer, Triplet
from monad.cognition.memory.query_router import QueryRouter, QueryMode

__all__ = ["MemoryLayer", "Triplet", "QueryRouter", "QueryMode"]
