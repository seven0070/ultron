"""Base classes for cognitive organs."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class OrganCategory(str, Enum):
    HUMAN_GENIUS = "human_genius"
    ANIMAL_EXTREME = "animal_extreme"
    MICROBIAL = "microbial"
    CONCEPTUAL = "conceptual"


@dataclass
class OrganResult:
    """Standard output of any organ's process()."""
    organ_name: str
    output: Any                                # organ-specific
    confidence: float = 0.5                    # 0.0 – 1.0
    votes: dict[str, float] = field(default_factory=dict)   # {option: weight}
    reasoning: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Organ(ABC):
    """
    An Organ is an OPERATOR — a specialized cognitive function.

    It is NOT a resident of the knowledge graph. It reads from and writes to
    the graph, but lives in Python. Think of it as a specialist consultant
    the Executive can call on.
    """
    name: str
    inspiration: str                # "Einstein", "Octopus", "Slime mold", "Reflection", …
    category: OrganCategory
    description: str
    node_types: list[str] = field(default_factory=list)     # graph node types it touches
    search_strategy: str = "hybrid"                          # graph_only|vector_only|hybrid|temporal
    enabled: bool = True

    @abstractmethod
    def process(self, prompt: str, context: dict | None = None) -> OrganResult:
        """Perform this organ's cognitive operation."""

    def info(self) -> dict:
        return {
            "name": self.name,
            "inspiration": self.inspiration,
            "category": self.category.value,
            "description": self.description,
            "node_types": self.node_types,
            "search_strategy": self.search_strategy,
            "enabled": self.enabled,
        }
