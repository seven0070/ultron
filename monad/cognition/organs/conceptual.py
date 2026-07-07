"""
Conceptual Framework organs — 4 total (from user's canonical spec).
"""

from __future__ import annotations

from monad.cognition.organs.base import OrganCategory
from monad.cognition.organs.stub import make_stub


CONCEPTUAL: list[tuple[str, str, str, list[str], str]] = [
    ("Reality Collapse Awareness", "Quantum Observer Effect",
     "Chooses what to observe; rest stays in superposition",
     ["ObservationChoice", "CollapsedState", "SuperposedAlternative"],
     "collapse_aware_retrieval"),
    ("Somatic Valuation", "Value Function",
     "Gut-level instantaneous marker for opportunity or threat",
     ["SomaticMarker", "PreCognitiveSignal"], "somatic_priority_ranking"),
    ("Physical Stakes Integration", "Embodied Cognition",
     "Feels capital losses and gains viscerally",
     ["EmbodiedSignal", "PhysicalStakesMapping"], "embodied_significance_search"),
    ("Meta-Prompt Architecture", "System Prompt Leaks",
     "Full self-knowledge of cognitive design",
     ["ArchitecturalInsight", "SelfDesignAwareness"], "meta_architecture_search"),
]

assert len(CONCEPTUAL) == 4, f"expected 4 conceptual organs, got {len(CONCEPTUAL)}"


def build_conceptual_organs() -> list:
    return [
        make_stub(
            name=name,
            inspiration=inspiration,
            category=OrganCategory.CONCEPTUAL,
            description=description,
            node_types=node_types,
            search_strategy=search_strategy,
        )
        for (name, inspiration, description, node_types, search_strategy) in CONCEPTUAL
    ]
