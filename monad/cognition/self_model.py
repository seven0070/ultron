"""
SelfModel — Layer 7. A SEPARATE meta-graph for metacognition.

Records:
  - what the system did (activations, decisions, cycles)
  - what worked / didn't (feedback)
  - conflicts and how they were resolved
  - beliefs about own capabilities (updated over time)

Kept in a SEPARATE graph so metacognition doesn't pollute domain memory.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class SelfNode:
    kind: str                                   # "cycle" | "activation" | "conflict" | "belief"
    label: str
    data: dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class SelfModel:
    """A metacognitive graph — nodes + typed edges."""

    def __init__(self) -> None:
        self._nodes: list[SelfNode] = []
        self._edges: list[tuple[int, int, str]] = []      # (src_idx, dst_idx, rel)
        self._built = False

    def build(self) -> "SelfModel":
        """Initialize with anchor 'self' belief nodes."""
        if self._built:
            return self
        self._nodes.append(SelfNode(kind="belief", label="I am Monad",
                                    data={"identity": "Monad", "version": "0.2.0"}))
        self._nodes.append(SelfNode(kind="belief", label="I use 83 organs",
                                    data={"organs_total": 83}))
        self._built = True
        return self

    # -- recording ------------------------------------------------------------

    def record_cycle(self, prompt: str, decision: dict) -> int:
        node = SelfNode(kind="cycle", label=f"Cycle: {prompt[:50]}",
                        data={"prompt": prompt, "decision": decision})
        self._nodes.append(node)
        return len(self._nodes) - 1

    def record_activation(self, organ_name: str, result: dict, cycle_idx: int | None = None) -> int:
        node = SelfNode(kind="activation", label=f"Activated: {organ_name}",
                        data={"organ": organ_name, "result": result})
        self._nodes.append(node)
        idx = len(self._nodes) - 1
        if cycle_idx is not None:
            self._edges.append((cycle_idx, idx, "activated"))
        return idx

    def add_conflict(self, description: str, options: list[str], resolution: str) -> int:
        node = SelfNode(kind="conflict", label=f"Conflict: {description[:50]}",
                        data={"description": description, "options": options,
                              "resolution": resolution})
        self._nodes.append(node)
        return len(self._nodes) - 1

    def add_belief(self, label: str, data: dict) -> int:
        node = SelfNode(kind="belief", label=label, data=data)
        self._nodes.append(node)
        return len(self._nodes) - 1

    # -- inspection -----------------------------------------------------------

    def nodes(self) -> list[SelfNode]:
        return list(self._nodes)

    def by_kind(self, kind: str) -> list[SelfNode]:
        return [n for n in self._nodes if n.kind == kind]

    def stats(self) -> dict[str, Any]:
        from collections import Counter
        counts = Counter(n.kind for n in self._nodes)
        return {"total_nodes": len(self._nodes), "total_edges": len(self._edges),
                "by_kind": dict(counts), "built": self._built}
