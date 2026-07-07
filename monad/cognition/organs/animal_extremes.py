"""
Animal Extreme organs — 6 total (from user's canonical spec).
"""

from __future__ import annotations

from monad.cognition.organs.base import OrganCategory
from monad.cognition.organs.stub import make_stub


ANIMAL_EXTREMES: list[tuple[str, str, str, list[str], str]] = [
    ("Quantum Field Perception", "Pigeon",
     "Senses invisible fields via magnetoreception",
     ["HiddenField", "MagneticAnomaly"], "field_perception_scan"),
    ("Adaptive Reprogramming", "Octopus",
     "Real-time RNA-level editing; immediate adaptation",
     ["AdaptationEvent", "ReprogrammingSite"], "adaptive_edit_search"),
    ("Regenerative Healing", "Axolotl",
     "Scarless rebuilding after catastrophic drawdowns",
     ["RecoveryPath", "RegenerationEvent"], "healing_path_trace"),
    ("Seismic Perception", "Elephant",
     "Detects tremors before visible movement",
     ["TremorSignal", "EarlyWarning"], "seismic_early_detection"),
    ("Hyperspectral Vision", "Mantis Shrimp",
     "Sees 16+ dimensions; strikes with cavitation force",
     ["HyperspectralDimension", "CavitationTrigger"], "hyperspectral_scan"),
    ("Phoenix Protocol", "Immortal Jellyfish",
     "Resets to known-good state preserving all lessons",
     ["ResetPoint", "PreservedLesson"], "phoenix_state_retrieval"),
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
