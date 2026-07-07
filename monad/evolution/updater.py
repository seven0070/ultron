"""
SelfUpdater — Level 1 self-improvement.

Pulls latest Monad code from its git remote (typically your GitHub repo).
NEVER touches models/, memory_data/, workspace/, cache/, logs/.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from monad.core.logger import get_logger

log = get_logger(__name__)


class SelfUpdater:
    def __init__(self, root: Path, remote: str = "origin", branch: str = "main") -> None:
        self.root = Path(root)
        self.remote = remote
        self.branch = branch

    def _git(self, *args: str) -> tuple[int, str, str]:
        proc = subprocess.run(
            ["git", *args],
            cwd=str(self.root),
            capture_output=True, text=True,
        )
        return proc.returncode, proc.stdout.strip(), proc.stderr.strip()

    def current_version(self) -> str:
        code, out, _ = self._git("describe", "--tags", "--always")
        return out if code == 0 else "unknown"

    def check_for_updates(self) -> dict:
        code, _, err = self._git("fetch", self.remote, self.branch)
        if code != 0:
            return {"available": False, "error": err or "git fetch failed"}

        _, local, _ = self._git("rev-parse", "HEAD")
        _, remote, _ = self._git("rev-parse", f"{self.remote}/{self.branch}")
        _, count, _ = self._git("rev-list", "--count", f"HEAD..{self.remote}/{self.branch}")

        return {
            "available": local != remote,
            "local": local[:12],
            "remote": remote[:12],
            "commits_behind": int(count) if count.isdigit() else 0,
        }

    def apply_update(self) -> dict:
        # Make sure working tree is clean — never overwrite user changes
        code, out, _ = self._git("status", "--porcelain")
        if out.strip():
            return {"ok": False, "reason": "working tree has uncommitted changes",
                    "details": out}

        code, out, err = self._git("pull", "--ff-only", self.remote, self.branch)
        return {
            "ok": code == 0,
            "output": out,
            "error": err,
            "new_version": self.current_version(),
        }
