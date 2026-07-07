"""
Animal Extreme organs — 6 total.

Inspired by animal cognition/sensing extremes that outperform humans in
specific niches.
"""

from __future__ import annotations

from monad.cognition.organs.base import OrganCategory
from monad.cognition.organs.stub import make_stub


ANIMAL_EXTREMES: list[tuple[str, str, str, list[str], str]] = [
    ("distributed_pattern_matcher", "Octopus",
     "Distributed processing — each 'arm' proposes independently, results merged.",
     ["Pattern","Proposal"], "hybrid"),

    ("echolocation_probe", "Bat",
     "Actively probe unknown space with test-queries and integrate returns.",
     ["Probe","Return"], "vector_only"),

    ("magnetic_navigator", "Pigeon",
     "Long-range orientation using stable-attractor cues, not turn-by-turn logic.",
     ["Landmark","Bearing"], "graph_only"),

    ("swarm_consensus", "Bee",
     "Waggle-dance style: many weak signals aggregate into a strong direction.",
     ["Signal","Consensus"], "hybrid"),

    ("infrared_predator", "Snake",
     "Detects hot-spots (anomalies) in otherwise cold data.",
     ["Anomaly"], "vector_only"),

    ("mimetic_learner", "Corvid",
     "Learns tool-use by observation and rapid transfer.",
     ["ToolUse","Imitation"], "graph_only"),
]

assert len(ANIMAL_EXTREMES) == 6, f"expected 6 animal extremes, got {len(ANIMAL_EXTREMES)}"


def build_animal_extreme_organs() -> list:
    return [
        make_stub(
            name=name,
            inspiration=inspiration,
            category=OrganCategory.ANIMAL_EXTREME,
            description=description,
            node_types=node_types,
            search_strategy=search_strategy,
        )
        for (name, inspiration, description, node_types, search_strategy) in ANIMAL_EXTREMES
    ]
