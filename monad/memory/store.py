"""
SQLite-backed key/value + episodic memory.

Two tables:
  kv        (key TEXT PRIMARY KEY, value TEXT, updated_at TEXT)
  events    (id INTEGER PK AUTOINCREMENT, ts TEXT, kind TEXT, tag TEXT,
             content TEXT, metadata JSON)

Everything is single-file, embedded, zero-config — perfect for USB portability.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from monad.core.logger import get_logger

log = get_logger(__name__)


@dataclass
class EpisodicEvent:
    id: int
    ts: str
    kind: str                        # "user_msg" | "assistant_msg" | "tool_use" | ...
    tag: str
    content: str
    metadata: dict = field(default_factory=dict)


class MemoryStore:
    """Real SQLite-backed store. Thread-safe via check_same_thread=False."""

    SCHEMA = """
    CREATE TABLE IF NOT EXISTS kv (
        key        TEXT PRIMARY KEY,
        value      TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS events (
        id        INTEGER PRIMARY KEY AUTOINCREMENT,
        ts        TEXT NOT NULL,
        kind      TEXT NOT NULL,
        tag       TEXT DEFAULT '',
        content   TEXT NOT NULL,
        metadata  TEXT
    );
    CREATE INDEX IF NOT EXISTS idx_events_ts   ON events(ts);
    CREATE INDEX IF NOT EXISTS idx_events_kind ON events(kind);
    CREATE INDEX IF NOT EXISTS idx_events_tag  ON events(tag);
    """

    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self._conn.executescript(self.SCHEMA)
        self._conn.commit()

    # -- key/value -----------------------------------------------------------

    def put(self, key: str, value: Any) -> None:
        v = value if isinstance(value, str) else json.dumps(value)
        self._conn.execute(
            "INSERT OR REPLACE INTO kv (key, value, updated_at) VALUES (?, ?, ?)",
            (key, v, datetime.now().isoformat()),
        )
        self._conn.commit()

    def get(self, key: str, default: Any = None) -> Any:
        cur = self._conn.execute("SELECT value FROM kv WHERE key = ?", (key,))
        row = cur.fetchone()
        if row is None:
            return default
        v = row[0]
        try:
            return json.loads(v)
        except (json.JSONDecodeError, TypeError):
            return v

    def delete(self, key: str) -> bool:
        cur = self._conn.execute("DELETE FROM kv WHERE key = ?", (key,))
        self._conn.commit()
        return cur.rowcount > 0

    def keys(self, prefix: str = "") -> list[str]:
        if prefix:
            cur = self._conn.execute(
                "SELECT key FROM kv WHERE key LIKE ? ORDER BY key",
                (prefix + "%",),
            )
        else:
            cur = self._conn.execute("SELECT key FROM kv ORDER BY key")
        return [r[0] for r in cur.fetchall()]

    # -- episodic events -----------------------------------------------------

    def append_event(self, kind: str, content: str, tag: str = "",
                     metadata: dict | None = None) -> int:
        cur = self._conn.execute(
            "INSERT INTO events (ts, kind, tag, content, metadata) VALUES (?, ?, ?, ?, ?)",
            (datetime.now().isoformat(), kind, tag, content,
             json.dumps(metadata or {})),
        )
        self._conn.commit()
        return cur.lastrowid

    def recent_events(self, limit: int = 50, kind: str | None = None,
                      tag: str | None = None) -> list[EpisodicEvent]:
        q = "SELECT id, ts, kind, tag, content, metadata FROM events"
        params: list = []
        clauses = []
        if kind:
            clauses.append("kind = ?"); params.append(kind)
        if tag:
            clauses.append("tag = ?"); params.append(tag)
        if clauses:
            q += " WHERE " + " AND ".join(clauses)
        q += " ORDER BY id DESC LIMIT ?"
        params.append(limit)
        cur = self._conn.execute(q, params)
        return [self._row_to_event(r) for r in cur.fetchall()]

    def search_events(self, needle: str, limit: int = 20) -> list[EpisodicEvent]:
        cur = self._conn.execute(
            "SELECT id, ts, kind, tag, content, metadata FROM events "
            "WHERE content LIKE ? ORDER BY id DESC LIMIT ?",
            (f"%{needle}%", limit),
        )
        return [self._row_to_event(r) for r in cur.fetchall()]

    def _row_to_event(self, r) -> EpisodicEvent:
        return EpisodicEvent(
            id=r[0], ts=r[1], kind=r[2], tag=r[3], content=r[4],
            metadata=json.loads(r[5]) if r[5] else {},
        )

    # -- housekeeping --------------------------------------------------------

    def size(self) -> dict:
        kv = self._conn.execute("SELECT COUNT(*) FROM kv").fetchone()[0]
        ev = self._conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
        return {"kv_keys": kv, "events": ev, "path": str(self.db_path)}

    def clear(self) -> None:
        self._conn.execute("DELETE FROM kv")
        self._conn.execute("DELETE FROM events")
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()


class Memory:
    """Convenience facade: MemoryStore + VectorStore + RetrievalEngine wired together."""

    def __init__(self, memory_dir: str | Path) -> None:
        from monad.memory.retrieval import RetrievalEngine
        from monad.memory.vector import VectorStore
        d = Path(memory_dir)
        d.mkdir(parents=True, exist_ok=True)
        self.store = MemoryStore(d / "memory.db")
        self.vectors = VectorStore(persist_dir=d / "vectors")
        self.retrieval = RetrievalEngine(self.store, self.vectors)

    def remember(self, content: str, kind: str = "note", tag: str = "",
                 metadata: dict | None = None) -> int:
        """Persist an event AND embed it for semantic search."""
        event_id = self.store.append_event(kind=kind, content=content, tag=tag,
                                            metadata=metadata)
        self.vectors.add(doc_id=f"event-{event_id}", text=content,
                         metadata={"kind": kind, "tag": tag, **(metadata or {})})
        return event_id

    def recall(self, query: str, top_k: int = 5) -> list:
        return self.retrieval.retrieve(query, top_k=top_k)

    def forget(self, needle: str) -> int:
        matches = self.store.search_events(needle, limit=1000)
        for m in matches:
            self.vectors.delete(f"event-{m.id}")
        # Delete from SQLite
        cur = self.store._conn.execute("DELETE FROM events WHERE content LIKE ?",
                                        (f"%{needle}%",))
        self.store._conn.commit()
        return cur.rowcount

    def size(self) -> dict:
        return {"store": self.store.size(), "vectors": self.vectors.size()}
