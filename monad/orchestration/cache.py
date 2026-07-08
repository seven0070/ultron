"""
Build #024 — Response cache.

Two-tier cache to avoid re-running the LLM on repeat prompts:

  L1  In-memory LRU  (fast, per-process)
  L2  SQLite         (persistent across restarts, ships on the USB)

Key = SHA256(model_id + prompt + generation_params).
Value = full text response + tokens + latency + metadata.

Skip conditions (never cache):
  - streams (nothing to hash yet)
  - responses with placeholder/stub markers
  - responses that clearly failed
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from monad.core.logger import get_logger

log = get_logger(__name__)


@dataclass
class CacheEntry:
    key: str
    text: str
    model_id: str
    tokens: int = 0
    latency_ms: float = 0.0
    hit_count: int = 0
    created_at: float = field(default_factory=time.time)
    last_hit_at: float = 0.0
    metadata: dict = field(default_factory=dict)


class ResponseCache:
    """Fast LRU + persistent SQLite cache for LLM responses."""

    SCHEMA = """
    CREATE TABLE IF NOT EXISTS response_cache (
        key         TEXT PRIMARY KEY,
        text        TEXT NOT NULL,
        model_id    TEXT NOT NULL,
        tokens      INTEGER DEFAULT 0,
        latency_ms  REAL DEFAULT 0,
        hit_count   INTEGER DEFAULT 0,
        created_at  REAL NOT NULL,
        last_hit_at REAL DEFAULT 0,
        metadata    TEXT
    );
    CREATE INDEX IF NOT EXISTS idx_cache_last_hit ON response_cache(last_hit_at);
    CREATE INDEX IF NOT EXISTS idx_cache_created  ON response_cache(created_at);
    """

    def __init__(
        self,
        db_path: str | Path | None = None,
        lru_size: int = 256,
        max_prompt_bytes: int = 100_000,
    ) -> None:
        self.db_path = Path(db_path) if db_path else None
        self.lru_size = lru_size
        self.max_prompt_bytes = max_prompt_bytes
        self._lru: OrderedDict[str, CacheEntry] = OrderedDict()
        self._conn: sqlite3.Connection | None = None

        if self.db_path is not None:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
            self._conn.executescript(self.SCHEMA)
            self._conn.commit()

    # -- key building ---------------------------------------------------------

    @staticmethod
    def make_key(model_id: str, prompt: str, **params) -> str:
        # Filter to deterministic sampling params only
        stable = {k: params.get(k) for k in
                  ("max_tokens", "temperature", "top_p", "stop") if k in params}
        payload = json.dumps({"m": model_id, "p": prompt, "x": stable},
                              sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    # -- get / put ------------------------------------------------------------

    def get(self, key: str) -> CacheEntry | None:
        # L1
        if key in self._lru:
            entry = self._lru[key]
            self._lru.move_to_end(key)
            entry.hit_count += 1
            entry.last_hit_at = time.time()
            log.debug("cache HIT L1: {}", key[:12])
            return entry

        # L2 (persistent)
        if self._conn is not None:
            cur = self._conn.execute(
                "SELECT key,text,model_id,tokens,latency_ms,hit_count,"
                "created_at,last_hit_at,metadata "
                "FROM response_cache WHERE key = ?", (key,),
            )
            row = cur.fetchone()
            if row is not None:
                entry = CacheEntry(
                    key=row[0], text=row[1], model_id=row[2],
                    tokens=row[3], latency_ms=row[4],
                    hit_count=row[5] + 1,
                    created_at=row[6], last_hit_at=time.time(),
                    metadata=json.loads(row[8]) if row[8] else {},
                )
                # Promote into LRU
                self._promote_to_lru(entry)
                self._conn.execute(
                    "UPDATE response_cache SET hit_count=?, last_hit_at=? WHERE key=?",
                    (entry.hit_count, entry.last_hit_at, key),
                )
                self._conn.commit()
                log.debug("cache HIT L2 → L1: {}", key[:12])
                return entry

        return None

    def put(self, entry: CacheEntry) -> None:
        if not entry.text or not entry.text.strip():
            return
        if self._should_skip(entry.text):
            return

        self._promote_to_lru(entry)

        if self._conn is not None:
            self._conn.execute(
                "INSERT OR REPLACE INTO response_cache "
                "(key,text,model_id,tokens,latency_ms,hit_count,"
                " created_at,last_hit_at,metadata) "
                "VALUES (?,?,?,?,?,?,?,?,?)",
                (entry.key, entry.text, entry.model_id, entry.tokens,
                 entry.latency_ms, entry.hit_count, entry.created_at,
                 entry.last_hit_at, json.dumps(entry.metadata)),
            )
            self._conn.commit()
        log.debug("cache PUT: {}", entry.key[:12])

    def _promote_to_lru(self, entry: CacheEntry) -> None:
        self._lru[entry.key] = entry
        self._lru.move_to_end(entry.key)
        while len(self._lru) > self.lru_size:
            self._lru.popitem(last=False)

    def _should_skip(self, text: str) -> bool:
        lowered = text.lower()
        if len(text) > self.max_prompt_bytes:
            return True
        markers = ("[stub", "[error", "[model not available", "[all proposers failed")
        return any(m in lowered for m in markers)

    # -- housekeeping ---------------------------------------------------------

    def size(self) -> dict:
        stats = {"lru_entries": len(self._lru), "lru_capacity": self.lru_size}
        if self._conn is not None:
            row = self._conn.execute(
                "SELECT COUNT(*), COALESCE(SUM(hit_count), 0) FROM response_cache",
            ).fetchone()
            stats["persisted_entries"] = row[0]
            stats["lifetime_hits"] = row[1]
        return stats

    def clear(self) -> int:
        n = len(self._lru)
        self._lru.clear()
        if self._conn is not None:
            cur = self._conn.execute("SELECT COUNT(*) FROM response_cache").fetchone()
            n += cur[0]
            self._conn.execute("DELETE FROM response_cache")
            self._conn.commit()
        return n

    def evict_older_than(self, days: float) -> int:
        if self._conn is None:
            return 0
        cutoff = time.time() - days * 86400
        cur = self._conn.execute(
            "DELETE FROM response_cache WHERE last_hit_at < ? AND created_at < ?",
            (cutoff, cutoff),
        )
        self._conn.commit()
        return cur.rowcount

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None
