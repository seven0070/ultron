"""
STUB tool framework. Real tools (filesystem, python sandbox, terminal, browser,
git, PDF, JCode, ZeroLang) land in Builds #036–#055.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class Tool(ABC):
    id: str = ""
    name: str = ""
    description: str = ""
    requires_approval: bool = True

    @abstractmethod
    def invoke(self, **kwargs) -> Any: ...


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        self._tools[tool.id] = tool

    def get(self, tool_id: str) -> Tool | None:
        return self._tools.get(tool_id)

    def list(self) -> list[Tool]:
        return list(self._tools.values())
