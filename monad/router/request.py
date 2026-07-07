"""Request / Response dataclasses."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from monad.router.intent import Intent


@dataclass
class Request:
    text: str
    session_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Response:
    text: str
    intent: Intent = Intent.UNKNOWN
    model_id: str = ""
    tokens: int = 0
    latency_ms: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)
