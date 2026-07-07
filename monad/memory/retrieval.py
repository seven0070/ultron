"""
RetrievalEngine — combines episodic (SQLite) + semantic (vector) with RRF fusion.

Uses Reciprocal Rank Fusion (Cormack et al., SIGIR 2009) — the standard 2026
technique for merging graph/keyword and vector results in a hybrid retriever.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class RetrievalResult:
    doc_id: str
    text: str
    score: float
    source: str                            # "keyword" | "vector" | "hybrid"
    metadata: dict = field(default_factory=dict)


class RetrievalEngine:
    """Unified retrieval across MemoryStore (SQLite) and VectorStore (semantic)."""

    def __init__(self, memory_store, vector_store, rrf_k: int = 60) -> None:
        self.memory = memory_store
        self.vectors = vector_store
        self.rrf_k = rrf_k          # RRF constant; 60 is Cormack's default

    def retrieve(self, query: str, top_k: int = 5,
                 mode: str = "hybrid") -> list[RetrievalResult]:
        if mode == "keyword":
            return self._keyword_only(query, top_k)
        if mode == "vector":
            return self._vector_only(query, top_k)
        return self._hybrid(query, top_k)

    # -- individual modes ----------------------------------------------------

    def _keyword_only(self, query: str, top_k: int) -> list[RetrievalResult]:
        events = self.memory.search_events(query, limit=top_k)
        out = []
        for i, e in enumerate(events):
            score = 1.0 / (self.rrf_k + i + 1)
            out.append(RetrievalResult(
                doc_id=f"event-{e.id}", text=e.content, score=round(score, 4),
                source="keyword", metadata={"kind": e.kind, "tag": e.tag, "ts": e.ts},
            ))
        return out

    def _vector_only(self, query: str, top_k: int) -> list[RetrievalResult]:
        hits = self.vectors.query(query, top_k=top_k)
        out = []
        for did, score, meta in hits:
            # Recover original text from metadata or SQLite lookup
            text = self._recover_text(did)
            out.append(RetrievalResult(
                doc_id=did, text=text, score=round(score, 4),
                source="vector", metadata=meta,
            ))
        return out

    def _hybrid(self, query: str, top_k: int) -> list[RetrievalResult]:
        keyword_hits = self._keyword_only(query, top_k=top_k * 2)
        vector_hits = self._vector_only(query, top_k=top_k * 2)

        # RRF fusion
        rrf_scores: dict[str, float] = {}
        best: dict[str, RetrievalResult] = {}

        for rank, r in enumerate(keyword_hits):
            rrf_scores[r.doc_id] = rrf_scores.get(r.doc_id, 0.0) + 1.0 / (self.rrf_k + rank + 1)
            best[r.doc_id] = r
        for rank, r in enumerate(vector_hits):
            rrf_scores[r.doc_id] = rrf_scores.get(r.doc_id, 0.0) + 1.0 / (self.rrf_k + rank + 1)
            if r.doc_id not in best:
                best[r.doc_id] = r

        ranked = sorted(rrf_scores.items(), key=lambda kv: -kv[1])[:top_k]
        results = []
        for did, score in ranked:
            r = best[did]
            results.append(RetrievalResult(
                doc_id=r.doc_id, text=r.text, score=round(score, 4),
                source="hybrid", metadata=r.metadata,
            ))
        return results

    # -- helpers -------------------------------------------------------------

    def _recover_text(self, doc_id: str) -> str:
        if doc_id.startswith("event-"):
            try:
                eid = int(doc_id.split("-", 1)[1])
                cur = self.memory._conn.execute(
                    "SELECT content FROM events WHERE id = ?", (eid,))
                row = cur.fetchone()
                return row[0] if row else ""
            except Exception:
                return ""
        return ""
