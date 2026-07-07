"""
Conceptual Framework organs — 4 total.

High-order cognitive frames, not tied to a specific person or organism.
"""

from __future__ import annotations

from monad.cognition.organs.base import OrganCategory
from monad.cognition.organs.stub import make_stub


CONCEPTUAL: list[tuple[str, str, str, list[str], str]] = [
    ("reflective_metacognition", "Reflection",
     "Reflexion pattern: generate → critique → revise.",
     ["Draft","Critique","Revision"], "hybrid"),
    ("counterfactual_reasoner", "Counterfactual",
     "Reasons about what-if / alternative worlds.",
     ["World","Alternative"], "graph_only"),
    ("dialectical_synthesizer", "Dialectic",
     "Thesis / antithesis / synthesis to resolve conflicts.",
     ["Thesis","Antithesis","Synthesis"], "graph_only"),
    ("first_principles_reset", "FirstPrinciples",
     "Discards received framings; rebuilds from axioms.",
     ["Axiom"], "graph_only"),
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
