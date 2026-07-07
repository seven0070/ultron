"""
EvolutionLog — SQLite-backed journal of every self-change.

Every proposal, every apply, every rollback is recorded. This is the audit
trail that lets you trust an evolving system.
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path


class ChangeType(str, Enum):
    UPDATE = "update"           # Level 1 — self-update from repo
    NEW_PLUGIN = "new_plugin"   # Level 2
    NEW_TOOL = "new_tool"       # Level 2
    PATCH_PROMPT = "patch_prompt"     # Level 2/3
    PATCH_CONFIG = "patch_config"     # Level 2/3
    PATCH_PLUGIN = "patch_plugin"     # Level 3
    PATCH_TOOL = "patch_tool"         # Level 3
    ROLLBACK = "rollback"


class Outcome(str, Enum):
    PROPOSED = "proposed"       # written but not applied
    APPROVED = "approved"       # user OK'd
    APPLIED = "applied"         # patch on disk
    ROLLED_BACK = "rolled_back"
    REJECTED = "rejected"       # user denied
    FAILED = "failed"           # tests failed / apply errored


@dataclass
class EvolutionRecord:
    id: str
    timestamp: str
    change_type: ChangeType
    outcome: Outcome
    goal: str                                   # why the change was proposed
    target_path: str                            # file affected
    diff: str                                   # unified diff (may be truncated)
    tests_passed: bool | None = None
    test_output: str = ""
    approver: str = "user"
    backup_path: str = ""
    parent_id: str = ""                         # links rollbacks to originals
    metadata: dict = field(default_factory=dict)


class EvolutionLog:
    SCHEMA = """
    CREATE TABLE IF NOT EXISTS evolution_records (
        id            TEXT PRIMARY KEY,
        timestamp     TEXT NOT NULL,
        change_type   TEXT NOT NULL,
        outcome       TEXT NOT NULL,
        goal          TEXT NOT NULL,
        target_path   TEXT NOT NULL,
        diff          TEXT,
        tests_passed  INTEGER,
        test_output   TEXT,
        approver      TEXT,
        backup_path   TEXT,
        parent_id     TEXT,
        metadata      TEXT
    );
    CREATE INDEX IF NOT EXISTS idx_evo_time ON evolution_records(timestamp);
    CREATE INDEX IF NOT EXISTS idx_evo_outcome ON evolution_records(outcome);
    """

    def __init__(self, db_path: Path) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self._conn.executescript(self.SCHEMA)
        self._conn.commit()

    def record(self, rec: EvolutionRecord) -> None:
        d = asdict(rec)
        d["change_type"] = rec.change_type.value
        d["outcome"] = rec.outcome.value
        d["tests_passed"] = None if rec.tests_passed is None else int(rec.tests_passed)
        d["metadata"] = json.dumps(rec.metadata)
        self._conn.execute(
            """INSERT OR REPLACE INTO evolution_records
               (id, timestamp, change_type, outcome, goal, target_path, diff,
                tests_passed, test_output, approver, backup_path, parent_id, metadata)
               VALUES (:id, :timestamp, :change_type, :outcome, :goal, :target_path,
                       :diff, :tests_passed, :test_output, :approver, :backup_path,
                       :parent_id, :metadata)""",
            d,
        )
        self._conn.commit()

    def update_outcome(self, record_id: str, outcome: Outcome,
                       tests_passed: bool | None = None,
                       test_output: str = "") -> None:
        self._conn.execute(
            """UPDATE evolution_records
               SET outcome = ?, tests_passed = ?, test_output = ?
               WHERE id = ?""",
            (outcome.value,
             None if tests_passed is None else int(tests_passed),
             test_output, record_id),
        )
        self._conn.commit()

    def get(self, record_id: str) -> EvolutionRecord | None:
        cur = self._conn.execute(
            "SELECT * FROM evolution_records WHERE id = ?", (record_id,)
        )
        row = cur.fetchone()
        return self._row_to_record(row) if row else None

    def history(self, limit: int = 50) -> list[EvolutionRecord]:
        cur = self._conn.execute(
            "SELECT * FROM evolution_records ORDER BY timestamp DESC LIMIT ?",
            (limit,),
        )
        return [self._row_to_record(r) for r in cur.fetchall()]

    def _row_to_record(self, row) -> EvolutionRecord:
        cols = [c[0] for c in self._conn.execute(
            "SELECT * FROM evolution_records LIMIT 0").description]
        d = dict(zip(cols, row))
        return EvolutionRecord(
            id=d["id"],
            timestamp=d["timestamp"],
            change_type=ChangeType(d["change_type"]),
            outcome=Outcome(d["outcome"]),
            goal=d["goal"],
            target_path=d["target_path"],
            diff=d["diff"] or "",
            tests_passed=None if d["tests_passed"] is None else bool(d["tests_passed"]),
            test_output=d["test_output"] or "",
            approver=d["approver"] or "user",
            backup_path=d["backup_path"] or "",
            parent_id=d["parent_id"] or "",
            metadata=json.loads(d["metadata"]) if d["metadata"] else {},
        )

    @staticmethod
    def new_id() -> str:
        return f"evo-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6]}"

    def close(self) -> None:
        self._conn.close()
