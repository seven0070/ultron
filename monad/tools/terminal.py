"""
TerminalTool — allowlisted subprocess execution.

Only commands in the allowlist can be run. This is intentional: LLMs cannot
be trusted to invoke arbitrary shell commands, and this tool sits behind
the PolicyGate anyway.
"""

from __future__ import annotations

import shlex
import shutil
import subprocess

from monad.tools.base import Tool, ToolResult


class TerminalTool(Tool):
    id = "terminal"
    name = "Terminal"
    description = "Run a whitelisted shell command with a timeout"
    requires_approval = True
    action = "exec"

    DEFAULT_ALLOWLIST = {
        "ls", "pwd", "echo", "cat", "head", "tail", "wc", "grep",
        "find", "which", "date", "uname", "df", "du", "ps",
        "python", "python3", "pip", "git",
    }
    DEFAULT_TIMEOUT_S = 15
    MAX_OUTPUT_BYTES = 200_000

    def __init__(self, allowlist: set[str] | None = None) -> None:
        self.allowlist = set(allowlist) if allowlist is not None else set(self.DEFAULT_ALLOWLIST)

    def invoke(self, command: str = "", timeout_s: float | None = None,
               **kwargs) -> ToolResult:
        if not command.strip():
            return ToolResult(tool=self.id, ok=False, error="empty command")
        try:
            parts = shlex.split(command)
        except ValueError as e:
            return ToolResult(tool=self.id, ok=False, error=f"parse error: {e}")
        if not parts:
            return ToolResult(tool=self.id, ok=False, error="empty command")
        exe = parts[0]
        if exe not in self.allowlist:
            return ToolResult(
                tool=self.id, ok=False,
                error=f"command '{exe}' not in allowlist: {sorted(self.allowlist)}",
            )
        if shutil.which(exe) is None:
            return ToolResult(tool=self.id, ok=False, error=f"command not found: {exe}")

        t = float(timeout_s or self.DEFAULT_TIMEOUT_S)
        try:
            proc = subprocess.run(parts, capture_output=True, text=True, timeout=t)
            stdout = proc.stdout[:self.MAX_OUTPUT_BYTES]
            stderr = proc.stderr[:self.MAX_OUTPUT_BYTES]
            return ToolResult(
                tool=self.id, ok=(proc.returncode == 0),
                output={"stdout": stdout, "stderr": stderr, "exit_code": proc.returncode},
                metadata={"command": command, "timeout_s": t},
                error="" if proc.returncode == 0 else f"exit {proc.returncode}",
            )
        except subprocess.TimeoutExpired:
            return ToolResult(tool=self.id, ok=False, error=f"timeout after {t}s")
