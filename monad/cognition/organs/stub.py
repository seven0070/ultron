"""
Generic stub organ — used until user pastes real 83-organ specifications.

Every stub organ:
  - accepts any prompt
  - returns a low-confidence "consulted" marker with its inspiration
  - is safe to enable in the executive (won't crash)
"""

from __future__ import annotations

from monad.cognition.organs.base import Organ, OrganCategory, OrganResult


class StubOrgan(Organ):
    """A placeholder organ. Fill in the real logic per-organ later."""

    def process(self, prompt: str, context: dict | None = None) -> OrganResult:
        # Deterministic low-confidence vote so ExecutiveController can still run
        return OrganResult(
            organ_name=self.name,
            output=(
                f"[stub organ '{self.name}' inspired by {self.inspiration} "
                f"consulted on: {prompt[:80]}…]"
            ),
            confidence=0.10,
            votes={},
            reasoning=(
                "STUB — awaiting real implementation from the 83-organ spec "
                "the user will provide."
            ),
            metadata={
                "stub": True,
                "category": self.category.value,
                "inspiration": self.inspiration,
                "search_strategy": self.search_strategy,
            },
        )


def make_stub(
    name: str,
    inspiration: str,
    category: OrganCategory,
    description: str = "",
    node_types: list[str] | None = None,
    search_strategy: str = "hybrid",
) -> StubOrgan:
    return StubOrgan(
        name=name,
        inspiration=inspiration,
        category=category,
        description=description or f"Stub organ inspired by {inspiration}.",
        node_types=node_types or [],
        search_strategy=search_strategy,
    )
