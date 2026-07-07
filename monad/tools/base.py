"""Tool ABC + registry + result type."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


class ToolError(Exception):
    """Raised when a tool cannot complete its action."""


@dataclass
class ToolResult:
    tool: str
    ok: bool
    output: Any = None
    error: str = ""
    metadata: dict = field(default_factory=dict)


class Tool(ABC):
    id: str = ""
    name: str = ""
    description: str = ""
    requires_approval: bool = True
    action: str = ""                 # "read" | "write" | "exec" | "net" — used by policy

    @abstractmethod
    def invoke(self, **kwargs) -> ToolResult:
        """Execute the tool."""

    def info(self) -> dict:
        return {"id": self.id, "name": self.name, "description": self.description,
                "requires_approval": self.requires_approval, "action": self.action}


class ToolRegistry:
    def __init__(self, policy_gate=None) -> None:
        self._tools: dict[str, Tool] = {}
        self.policy_gate = policy_gate

    def register(self, tool: Tool) -> None:
        if not tool.id:
            raise ValueError("Tool must have an id")
        self._tools[tool.id] = tool

    def get(self, tool_id: str) -> Tool:
        if tool_id not in self._tools:
            raise KeyError(f"No such tool: {tool_id}")
        return self._tools[tool_id]

    def list(self) -> list[Tool]:
        return list(self._tools.values())

    def invoke(self, tool_id: str, **kwargs) -> ToolResult:
        """Invoke a tool through the policy gate (if one is set)."""
        tool = self.get(tool_id)
        if tool.requires_approval and self.policy_gate is not None:
            action_key = f"tool.{tool.id}.{tool.action or 'invoke'}"
            allowed = self.policy_gate.check(action_key, tool=tool.id, kwargs=kwargs)
            if not allowed:
                return ToolResult(tool=tool.id, ok=False,
                                  error=f"Denied by policy gate: {action_key}")
        try:
            return tool.invoke(**kwargs)
        except ToolError as e:
            return ToolResult(tool=tool.id, ok=False, error=str(e))
        except Exception as e:  # noqa: BLE001
            return ToolResult(tool=tool.id, ok=False, error=f"unexpected: {e}")
