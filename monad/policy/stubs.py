"""STUB approval gate."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ApprovalRequest:
    action: str
    reason: str
    details: dict


class PolicyGate:
    def __init__(self, require_approval_for: list[str] | None = None) -> None:
        self.require_approval_for = set(require_approval_for or [])

    def check(self, action: str, **details) -> bool:
        """Return True if action is allowed, False if it must be denied.
        In a real implementation this triggers user approval in the CLI/dashboard."""
        if action in self.require_approval_for:
            # STUB: always approve for now — real gate will prompt the user.
            return True
        return True
