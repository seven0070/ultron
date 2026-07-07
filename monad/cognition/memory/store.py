"""
Memory layer with optional Cognee backend.

Public API (Cognee 1.0-flavored aliases on top of the real add/cognify/search):
    remember(text)         → alias for add + cognify
    recall(query, mode)    → alias for search
    improve(feedback)      → future: reinforcement / weighting
    forget(node_id)        → deletion

If Cognee isn't installed, an in-memory triplet store handles everything.
The API surface is identical either way.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

try:
    import cognee                      # type: ignore
    HAVE_COGNEE = True
except Exception:
    HAVE_COGNEE = False


@dataclass
class Triplet:
    subject: str
    predicate: str
    object: str
    source: str = "user"
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    weight: float = 1.0

    def as_text(self) -> str:
        return f"{self.subject} {self.predicate} {self.object}"


class MemoryLayer:
    """Layer 2 of the cognitive architecture — persistent memory + retrieval."""

    def __init__(self, backend: str = "auto") -> None:
        """
        backend: "auto" | "cognee" | "inmem"
        """
        if backend == "cognee" and not HAVE_COGNEE:
            raise RuntimeError("Cognee backend requested but cognee is not installed. "
                               "pip install cognee")
        self.backend = "cognee" if (backend != "inmem" and HAVE_COGNEE) else "inmem"
        self._triplets: list[Triplet] = []
        self._raw_docs: list[tuple[str, str]] = []       # (id, text)

    # -- Cognee 1.0-flavored aliases -----------------------------------------

    def remember(self, text: str, source: str = "user") -> None:
        """Alias for add + cognify. Extracts naive triplets locally as a fallback."""
        self._raw_docs.append((f"doc-{len(self._raw_docs)}", text))
        for t in self._naive_triplets(text, source=source):
            self._triplets.append(t)

        if self.backend == "cognee":
            try:
                cognee.add(text)                          # type: ignore
                # cognify is async in real cognee; keep it optional
                if hasattr(cognee, "cognify"):
                    try:
                        cognee.cognify()                  # type: ignore
                    except Exception:
                        pass
            except Exception:
                pass       # graceful — fall through to in-mem

    def recall(self, query: str, mode: str = "hybrid", top_k: int = 5) -> list[dict]:
        """Recall matching memories. Returns list of {text, score, source, mode}."""
        if self.backend == "cognee":
            try:
                results = cognee.search(query)            # type: ignore
                out = []
                for r in list(results)[:top_k]:
                    out.append({"text": str(r), "score": 1.0,
                                "source": "cognee", "mode": mode})
                if out:
                    return out
            except Exception:
                pass
        return self._inmem_recall(query, top_k=top_k, mode=mode)

    def improve(self, node_or_triplet: str, feedback: float) -> None:
        """Weight a memory up or down based on downstream success."""
        for t in self._triplets:
            if node_or_triplet.lower() in t.as_text().lower():
                t.weight = max(0.0, min(5.0, t.weight + feedback))

    def forget(self, needle: str) -> int:
        """Remove memories matching a substring. Returns count removed."""
        before = len(self._triplets)
        self._triplets = [t for t in self._triplets
                          if needle.lower() not in t.as_text().lower()]
        self._raw_docs = [(i, d) for i, d in self._raw_docs
                          if needle.lower() not in d.lower()]
        return before - len(self._triplets)

    # -- introspection --------------------------------------------------------

    def size(self) -> dict:
        return {
            "backend": self.backend,
            "triplets": len(self._triplets),
            "docs": len(self._raw_docs),
        }

    def triplets(self) -> list[Triplet]:
        return list(self._triplets)

    # -- internals ------------------------------------------------------------

    _SVO_RE = re.compile(
        r"\b([A-Z][\w-]+)\s+(is|was|has|had|created|founded|discovered|wrote|invented|"
        r"designed|built|proved|solved|studies|studied)\s+([A-Za-z][\w -]+?)(?:\.|$)",
    )

    def _naive_triplets(self, text: str, source: str) -> list[Triplet]:
        out: list[Triplet] = []
        for m in self._SVO_RE.finditer(text):
            out.append(Triplet(m.group(1), m.group(2).lower(), m.group(3).strip(),
                               source=source))
        return out

    def _inmem_recall(self, query: str, top_k: int, mode: str) -> list[dict]:
        q = query.lower()
        scored: list[tuple[float, dict]] = []

        for t in self._triplets:
            text = t.as_text()
            score = _string_score(q, text.lower()) * t.weight
            if score > 0:
                scored.append((score, {
                    "text": text, "score": score, "source": t.source,
                    "mode": mode, "kind": "triplet",
                }))

        for _id, doc in self._raw_docs:
            score = _string_score(q, doc.lower())
            if score > 0:
                scored.append((score, {
                    "text": doc[:280], "score": score, "source": _id,
                    "mode": mode, "kind": "doc",
                }))

        scored.sort(key=lambda x: -x[0])
        return [entry for _, entry in scored[:top_k]]


def _string_score(query: str, text: str) -> float:
    """Cheap substring + token overlap score."""
    if not query or not text:
        return 0.0
    if query in text:
        return 1.0
    q_tokens = set(query.split())
    t_tokens = set(text.split())
    if not q_tokens:
        return 0.0
    overlap = len(q_tokens & t_tokens) / len(q_tokens)
    return overlap * 0.7
