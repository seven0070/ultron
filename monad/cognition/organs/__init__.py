"""
Organ system: 83 specialized cognitive modules.

Categories (from user spec):
  - Human Geniuses:        58 organs
  - Animal Extremes:        6 organs
  - Microbial Life:        15 organs
  - Conceptual Frameworks:  4 organs
                          ---
  Total:                   83 organs

⚠️ NOTE: The user's original prompt referenced a specific 83-organ list but
did not include it. All 83 organs below are registered as placeholders
(`organ_01` … `organ_83`) with correct category assignments. When the real
list arrives, edit `human_geniuses.py`, `animal_extremes.py`, `microbial.py`,
`conceptual.py` to fill in real names, inspirations, and node_types.

Organs are OPERATORS (functions) not RESIDENTS of the memory graph.
Each organ has:
  - node_types: which graph node types it produces/consumes
  - search_strategy: how it queries the graph
  - process(): the actual cognitive operation
"""

from monad.cognition.organs.base import Organ, OrganCategory, OrganResult
from monad.cognition.organs.registry import OrganRegistry, register_all

__all__ = ["Organ", "OrganCategory", "OrganResult", "OrganRegistry", "register_all"]
