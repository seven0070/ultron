"""
VectorStore — semantic search over embeddings.

Prefers ChromaDB (persistent, HNSW-indexed). Falls back to a pure-Python
cosine-similarity index that hashes text to a 128-dim vector — good enough
for keyword-adjacent retrieval and lets tests pass anywhere.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any

from monad.core.logger import get_logger

log = get_logger(__name__)


try:
    import chromadb                               # type: ignore
    HAVE_CHROMA = True
except Exception:
    HAVE_CHROMA = False


class VectorStore:
    def __init__(self, persist_dir: str | Path, collection: str = "monad") -> None:
        self.persist_dir = Path(persist_dir)
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self.collection_name = collection
        self.backend = "chroma" if HAVE_CHROMA else "hash"

        if self.backend == "chroma":
            try:
                self._client = chromadb.PersistentClient(path=str(self.persist_dir))
                self._collection = self._client.get_or_create_collection(collection)
                log.debug("VectorStore: ChromaDB at {}", self.persist_dir)
            except Exception as e:
                log.warning("ChromaDB init failed ({}), falling back to hash index", e)
                self.backend = "hash"

        if self.backend == "hash":
            self._fallback_path = self.persist_dir / "vectors.jsonl"
            self._docs: dict[str, tuple[str, dict, list[float]]] = {}
            self._load_fallback()
            log.debug("VectorStore: pure-Python hash index at {}", self._fallback_path)

    # -- public API ----------------------------------------------------------

    def add(self, doc_id: str, text: str, metadata: dict | None = None) -> None:
        metadata = metadata or {}
        if self.backend == "chroma":
            try:
                self._collection.upsert(
                    ids=[doc_id], documents=[text], metadatas=[metadata],
                )
                return
            except Exception as e:
                log.warning("chroma upsert failed: {}", e)
        # Fallback
        emb = _hash_embed(text)
        self._docs[doc_id] = (text, metadata, emb)
        self._save_fallback()

    def query(self, text: str, top_k: int = 5) -> list[tuple[str, float, dict]]:
        """Return list of (doc_id, score, metadata). Score is 0.0–1.0 (higher = better)."""
        if self.backend == "chroma":
            try:
                results = self._collection.query(query_texts=[text], n_results=top_k)
                ids = (results.get("ids") or [[]])[0]
                dists = (results.get("distances") or [[0.0] * len(ids)])[0]
                metas = (results.get("metadatas") or [[{}] * len(ids)])[0]
                out = []
                for did, dist, meta in zip(ids, dists, metas):
                    score = max(0.0, 1.0 - dist)
                    out.append((did, round(score, 4), meta or {}))
                return out
            except Exception as e:
                log.warning("chroma query failed: {}", e)
        # Fallback
        q_emb = _hash_embed(text)
        scored = []
        for did, (doc_text, meta, emb) in self._docs.items():
            score = _cosine(q_emb, emb)
            # Bonus for substring overlap (fights the weakness of hash-embeddings)
            if text.lower() in doc_text.lower():
                score = min(1.0, score + 0.3)
            scored.append((did, round(score, 4), meta))
        scored.sort(key=lambda t: -t[1])
        return scored[:top_k]

    def delete(self, doc_id: str) -> bool:
        if self.backend == "chroma":
            try:
                self._collection.delete(ids=[doc_id])
                return True
            except Exception as e:
                log.warning("chroma delete failed: {}", e)
                return False
        popped = self._docs.pop(doc_id, None)
        if popped is not None:
            self._save_fallback()
        return popped is not None

    def size(self) -> dict:
        if self.backend == "chroma":
            try:
                return {"backend": "chroma", "count": self._collection.count()}
            except Exception:
                pass
        return {"backend": self.backend, "count": len(self._docs)}

    # -- fallback persistence ------------------------------------------------

    def _load_fallback(self) -> None:
        if not self._fallback_path.exists():
            return
        try:
            with self._fallback_path.open("r", encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    rec = json.loads(line)
                    self._docs[rec["id"]] = (rec["text"], rec.get("meta", {}), rec["emb"])
        except Exception as e:
            log.warning("failed to load fallback vectors: {}", e)

    def _save_fallback(self) -> None:
        try:
            with self._fallback_path.open("w", encoding="utf-8") as fh:
                for did, (text, meta, emb) in self._docs.items():
                    fh.write(json.dumps({"id": did, "text": text,
                                         "meta": meta, "emb": emb}) + "\n")
        except Exception as e:
            log.warning("failed to save fallback vectors: {}", e)


# ---------------------------------------------------------------------------
# Cheap fallback embedding: hashed n-gram bag-of-words → 128-dim
# ---------------------------------------------------------------------------

_DIM = 128


def _hash_embed(text: str) -> list[float]:
    """Deterministic 128-dim embedding based on hashed word/bigram frequencies."""
    vec = [0.0] * _DIM
    tokens = _tokenize(text)
    for tok in tokens:
        h = int(hashlib.md5(tok.encode("utf-8")).hexdigest(), 16)
        vec[h % _DIM] += 1.0
    # Add bigrams
    for a, b in zip(tokens, tokens[1:]):
        h = int(hashlib.md5(f"{a}_{b}".encode("utf-8")).hexdigest(), 16)
        vec[h % _DIM] += 0.5
    # L2 normalize
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


def _tokenize(text: str) -> list[str]:
    import re
    return [t for t in re.findall(r"[a-z0-9]+", text.lower()) if len(t) > 1]


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    return max(0.0, min(1.0, dot))
