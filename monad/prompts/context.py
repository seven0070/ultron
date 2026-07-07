"""PromptContext — holds variables injected into templates."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class PromptContext:
    variables: dict[str, Any] = field(default_factory=dict)
    system: str = ""
    history: list[dict[str, str]] = field(default_factory=list)

    def set(self, key: str, value: Any) -> "PromptContext":
        self.variables[key] = value
        return self
