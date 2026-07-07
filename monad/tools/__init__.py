"""
Tool framework — Build #036–#040.

Real tools with policy-gated invocation:
  - FilesystemTool  (read, write, list, delete — sandboxed to workspace/)
  - PythonSandboxTool (exec arbitrary code in isolated subprocess with timeout)
  - TerminalTool    (safe subprocess with allowlist)
  - HTTPTool        (requests via stdlib urllib, size + host restrictions)

All tools declare `requires_approval` — a real PolicyGate can prompt the user
before invocation. See monad/policy/ for the gate.
"""

from monad.tools.base import Tool, ToolRegistry, ToolResult, ToolError
from monad.tools.filesystem import FilesystemTool
from monad.tools.python_sandbox import PythonSandboxTool
from monad.tools.terminal import TerminalTool
from monad.tools.http import HTTPTool

__all__ = [
    "Tool", "ToolRegistry", "ToolResult", "ToolError",
    "FilesystemTool", "PythonSandboxTool", "TerminalTool", "HTTPTool",
]


def default_registry(workspace_dir=None, policy_gate=None) -> ToolRegistry:
    """Convenience: pre-populated registry with all built-in tools."""
    reg = ToolRegistry(policy_gate=policy_gate)
    reg.register(FilesystemTool(workspace_dir=workspace_dir))
    reg.register(PythonSandboxTool())
    reg.register(TerminalTool())
    reg.register(HTTPTool())
    return reg
