"""
SandboxRunner — apply a patch in a throwaway copy and run tests.

If tests pass → the patch is safe to apply to the real tree.
If tests fail → we reject and log the failure.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

from monad.core.logger import get_logger

log = get_logger(__name__)


@dataclass
class SandboxResult:
    passed: bool
    exit_code: int
    stdout: str
    stderr: str
    duration_s: float


class SandboxRunner:
    """Copy the repo to a temp dir, apply the patch there, run pytest."""

    # Directories we skip when copying (fast + safe)
    SKIP = {".git", ".venv", "venv", "__pycache__", ".pytest_cache",
            "python_portable", "logs", "cache", "models", "memory_data",
            "workspace", "dist", "build"}

    def __init__(self, root: Path, python_exe: str | None = None,
                 test_command: list[str] | None = None) -> None:
        self.root = Path(root)
        self.python_exe = python_exe or sys.executable
        self.test_command = test_command or [self.python_exe, "-m", "pytest",
                                             "-x", "--tb=short", "-q"]

    def run(self, proposal) -> SandboxResult:
        """proposal has .target_path and .proposed_content"""
        import time
        start = time.time()

        with tempfile.TemporaryDirectory(prefix="monad-sandbox-") as tmp:
            sandbox = Path(tmp) / "monad"
            self._mirror_repo(self.root, sandbox)

            # Apply proposal
            target = sandbox / proposal.target_path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(proposal.proposed_content, encoding="utf-8")
            log.debug("Applied proposal in sandbox: {}", target)

            # Run tests
            try:
                proc = subprocess.run(
                    self.test_command,
                    cwd=str(sandbox),
                    capture_output=True,
                    text=True,
                    timeout=120,
                )
                return SandboxResult(
                    passed=(proc.returncode == 0),
                    exit_code=proc.returncode,
                    stdout=proc.stdout[-4000:],   # tail
                    stderr=proc.stderr[-2000:],
                    duration_s=round(time.time() - start, 2),
                )
            except subprocess.TimeoutExpired:
                return SandboxResult(
                    passed=False, exit_code=-1, stdout="",
                    stderr="TIMEOUT: tests exceeded 120s",
                    duration_s=round(time.time() - start, 2),
                )
            except FileNotFoundError as e:
                return SandboxResult(
                    passed=False, exit_code=-2, stdout="",
                    stderr=f"pytest not installed in sandbox: {e}",
                    duration_s=round(time.time() - start, 2),
                )

    def _mirror_repo(self, src: Path, dst: Path) -> None:
        """Fast shallow-ish copy — skips heavy directories."""
        dst.mkdir(parents=True, exist_ok=True)
        for item in src.iterdir():
            if item.name in self.SKIP:
                continue
            target = dst / item.name
            if item.is_dir():
                shutil.copytree(
                    item, target,
                    ignore=shutil.ignore_patterns(*self.SKIP, "*.pyc"),
                    dirs_exist_ok=True,
                )
            else:
                shutil.copy2(item, target)
