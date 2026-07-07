"""
PythonSandboxTool — execute Python in an isolated subprocess with timeout.

Uses a fresh interpreter, an empty environment, and a hard wall-clock timeout.
Not a security sandbox (a determined attacker can escape); the safety comes
from the PolicyGate requiring approval BEFORE invocation.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile

from monad.tools.base import Tool, ToolResult


class PythonSandboxTool(Tool):
    id = "python"
    name = "Python Sandbox"
    description = "Run Python code in an isolated subprocess with a hard timeout"
    requires_approval = True
    action = "exec"

    DEFAULT_TIMEOUT_S = 10
    MAX_OUTPUT_BYTES = 200_000

    def invoke(self, code: str = "", timeout_s: float | None = None,
               **kwargs) -> ToolResult:
        if not code.strip():
            return ToolResult(tool=self.id, ok=False, error="empty code")
        t = float(timeout_s or self.DEFAULT_TIMEOUT_S)

        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as fh:
            fh.write(code)
            script_path = fh.name
        try:
            proc = subprocess.run(
                [sys.executable, "-I", script_path],   # -I: isolated mode
                capture_output=True, text=True, timeout=t,
                env={"PATH": os.environ.get("PATH", ""),
                     "PYTHONDONTWRITEBYTECODE": "1"},
            )
            stdout = proc.stdout[:self.MAX_OUTPUT_BYTES]
            stderr = proc.stderr[:self.MAX_OUTPUT_BYTES]
            return ToolResult(
                tool=self.id,
                ok=(proc.returncode == 0),
                output={"stdout": stdout, "stderr": stderr},
                metadata={"exit_code": proc.returncode, "timeout_s": t},
                error="" if proc.returncode == 0
                      else f"exit {proc.returncode}: {stderr[:400]}",
            )
        except subprocess.TimeoutExpired:
            return ToolResult(tool=self.id, ok=False,
                              error=f"timeout after {t}s",
                              metadata={"timeout_s": t})
        finally:
            try:
                os.unlink(script_path)
            except OSError:
                pass
