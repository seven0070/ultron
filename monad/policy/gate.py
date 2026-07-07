"""
PolicyGate — approval-gated actions with a real audit trail.

Modes:
  ALLOW    - action allowed without prompt (dev only)
  DENY     - action always denied
  PROMPT   - synchronously prompt user (CLI)
  AUTO_YES - non-interactive tests / trusted flows
  AUTO_NO  - dry-run / safety-critical envs

Every check is journaled — same audit-trail principle as the evolution log.
"""

from __future__ import annotations

import json
import os
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Callable

from monad.core.logger import get_logger

log = get_logger(__name__)


class ApprovalMode(str, Enum):
    ALLOW = "allow"
    DENY = "deny"
    PROMPT = "prompt"
    AUTO_YES = "auto_yes"
    AUTO_NO = "auto_no"


class PolicyDecision(str, Enum):
    ALLOWED = "allowed"
    DENIED = "denied"
    PROMPT_APPROVED = "prompt_approved"
    PROMPT_REJECTED = "prompt_rejected"
    NOT_APPLICABLE = "not_applicable"


@dataclass
class ApprovalRequest:
    action: str
    reason: str = ""
    details: dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class PolicyGate:
    """The single decision point for every impactful action."""

    def __init__(
        self,
        require_approval_for: list[str] | None = None,
        default_mode: ApprovalMode = ApprovalMode.PROMPT,
        audit_db: str | Path | None = None,
        prompt_fn: Callable[[ApprovalRequest], bool] | None = None,
    ) -> None:
        self.require_approval_for: set[str] = set(require_approval_for or [])
        self.default_mode = default_mode
        self._per_action_mode: dict[str, ApprovalMode] = {}
        self._prompt_fn = prompt_fn or self._default_prompt
        self._audit = _AuditLog(audit_db) if audit_db else None

    # -- config --------------------------------------------------------------

    def set_mode(self, action: str, mode: ApprovalMode) -> None:
        self._per_action_mode[action] = mode

    def add_required(self, *actions: str) -> None:
        self.require_approval_for.update(actions)

    # -- the gate ------------------------------------------------------------

    def check(self, action: str, reason: str = "", **details) -> bool:
        """Return True if action is allowed, False if denied."""
        needs_check = (action in self.require_approval_for
                       or any(action.startswith(p) for p in self.require_approval_for))
        if not needs_check:
            self._journal(action, PolicyDecision.NOT_APPLICABLE, reason, details)
            return True

        mode = self._per_action_mode.get(action, self.default_mode)

        if mode == ApprovalMode.ALLOW:
            decision = PolicyDecision.ALLOWED
            approved = True
        elif mode == ApprovalMode.DENY:
            decision = PolicyDecision.DENIED
            approved = False
        elif mode == ApprovalMode.AUTO_YES:
            decision = PolicyDecision.ALLOWED
            approved = True
        elif mode == ApprovalMode.AUTO_NO:
            decision = PolicyDecision.DENIED
            approved = False
        else:  # PROMPT
            req = ApprovalRequest(action=action, reason=reason, details=details)
            approved = bool(self._prompt_fn(req))
            decision = (PolicyDecision.PROMPT_APPROVED if approved
                        else PolicyDecision.PROMPT_REJECTED)

        self._journal(action, decision, reason, details)
        log.info("PolicyGate: action={} decision={} mode={}",
                 action, decision.value, mode.value)
        return approved

    # -- prompt (default) ----------------------------------------------------

    def _default_prompt(self, req: ApprovalRequest) -> bool:
        # Environment override for CI / non-TTY
        env = os.environ.get("MONAD_POLICY_DEFAULT", "").lower()
        if env in ("y", "yes", "1", "true", "allow"):
            return True
        if env in ("n", "no", "0", "false", "deny"):
            return False

        try:
            print()
            print("=" * 60)
            print(f"  APPROVAL REQUIRED — action: {req.action}")
            if req.reason:
                print(f"  reason: {req.reason}")
            for k, v in (req.details or {}).items():
                s = str(v)
                if len(s) > 200:
                    s = s[:200] + "…"
                print(f"    {k}: {s}")
            print("=" * 60)
            answer = input("Approve? [y/N] ").strip().lower()
            return answer in ("y", "yes")
        except (EOFError, KeyboardInterrupt):
            return False

    # -- audit ---------------------------------------------------------------

    def _journal(self, action: str, decision: PolicyDecision,
                 reason: str, details: dict) -> None:
        if self._audit is None:
            return
        self._audit.record(action=action, decision=decision.value,
                           reason=reason, details=details)

    def audit_history(self, limit: int = 50) -> list[dict]:
        if self._audit is None:
            return []
        return self._audit.history(limit=limit)


class _AuditLog:
    SCHEMA = """
    CREATE TABLE IF NOT EXISTS policy_audit (
        id        INTEGER PRIMARY KEY AUTOINCREMENT,
        ts        TEXT NOT NULL,
        action    TEXT NOT NULL,
        decision  TEXT NOT NULL,
        reason    TEXT,
        details   TEXT
    );
    CREATE INDEX IF NOT EXISTS idx_policy_ts ON policy_audit(ts);
    """

    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self._conn.executescript(self.SCHEMA)
        self._conn.commit()

    def record(self, action: str, decision: str, reason: str, details: dict) -> None:
        self._conn.execute(
            "INSERT INTO policy_audit (ts, action, decision, reason, details) "
            "VALUES (?, ?, ?, ?, ?)",
            (datetime.now().isoformat(), action, decision, reason,
             json.dumps(details, default=str)),
        )
        self._conn.commit()

    def history(self, limit: int) -> list[dict]:
        cur = self._conn.execute(
            "SELECT ts, action, decision, reason, details "
            "FROM policy_audit ORDER BY id DESC LIMIT ?",
            (limit,),
        )
        return [
            {"ts": r[0], "action": r[1], "decision": r[2],
             "reason": r[3], "details": json.loads(r[4]) if r[4] else {}}
            for r in cur.fetchall()
        ]
