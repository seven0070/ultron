"""
OrganRegistry — central index of all 83 organs.
"""

from __future__ import annotations

from monad.cognition.organs.animal_extremes import build_animal_extreme_organs
from monad.cognition.organs.base import Organ, OrganCategory
from monad.cognition.organs.conceptual import build_conceptual_organs
from monad.cognition.organs.human_geniuses import build_human_genius_organs
from monad.cognition.organs.microbial import build_microbial_organs


class OrganRegistry:
    """Registry of all cognitive organs.

    - register_all()          → registers all 83 built-in organs
    - register(organ)         → add a custom organ
    - get(name)               → fetch by name
    - list_by_category(cat)   → filter by OrganCategory
    - enabled_only()          → active organs only
    - counts()                → {category: count}
    """

    def __init__(self) -> None:
        self._organs: dict[str, Organ] = {}

    # -- registration --------------------------------------------------------

    def register(self, organ: Organ) -> None:
        if not organ.name:
            raise ValueError("Organ must have a name")
        if organ.name in self._organs:
            raise ValueError(f"Duplicate organ name: {organ.name}")
        self._organs[organ.name] = organ

    def register_all(self) -> "OrganRegistry":
        """Build + register every built-in organ. Chainable."""
        for organ in (
            *build_human_genius_organs(),
            *build_animal_extreme_organs(),
            *build_microbial_organs(),
            *build_conceptual_organs(),
        ):
            self.register(organ)
        return self

    # -- lookups -------------------------------------------------------------

    def get(self, name: str) -> Organ:
        if name not in self._organs:
            raise KeyError(f"No such organ: {name}")
        return self._organs[name]

    def has(self, name: str) -> bool:
        return name in self._organs

    def all(self) -> list[Organ]:
        return list(self._organs.values())

    def list_by_category(self, category: OrganCategory) -> list[Organ]:
        return [o for o in self._organs.values() if o.category == category]

    def enabled_only(self) -> list[Organ]:
        return [o for o in self._organs.values() if o.enabled]

    def counts(self) -> dict[str, int]:
        out = {c.value: 0 for c in OrganCategory}
        for o in self._organs.values():
            out[o.category.value] += 1
        out["total"] = len(self._organs)
        return out

    def __len__(self) -> int:
        return len(self._organs)

    def __contains__(self, name: str) -> bool:
        return name in self._organs


def register_all() -> OrganRegistry:
    """Convenience: build a fully-populated registry."""
    return OrganRegistry().register_all()
