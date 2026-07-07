"""Perception layer — Layer 1. Normalizes any input into a standard signal."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Percept:
    modality: str                             # text | image | audio | file | other
    text: str
    raw: Any = None
    metadata: dict = field(default_factory=dict)


class PerceptionLayer:
    """Cheap normalization. Vision/audio adapters go here when tools land."""

    def perceive(self, input_data: Any) -> Percept:
        if isinstance(input_data, str):
            return Percept(modality="text", text=input_data)
        if isinstance(input_data, dict) and "text" in input_data:
            return Percept(
                modality=input_data.get("modality", "text"),
                text=str(input_data["text"]),
                raw=input_data.get("raw"),
                metadata={k: v for k, v in input_data.items()
                          if k not in ("text", "raw", "modality")},
            )
        return Percept(modality="other", text=str(input_data), raw=input_data)
