"""
ExecutiveController — orchestrates organs and resolves conflicts.

Strategies:
    weighted_vote        — combine organ outputs by (confidence × votes)
    highest_confidence   — pick the single most confident organ

Executive v2 additions (Phase 6):
    - per-organ model tier via ModelRouter
    - triggers Reflexion on low-confidence signals
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

from monad.cognition.organs.base import Organ, OrganResult


@dataclass
class ExecutiveDecision:
    strategy: str
    final_output: str
    winning_organs: list[str] = field(default_factory=list)
    tally: dict[str, float] = field(default_factory=dict)
    confidence: float = 0.0
    reflexion_triggered: bool = False
    conflicts: list[dict] = field(default_factory=list)


class ExecutiveController:
    def __init__(
        self,
        strategy: str = "weighted_vote",
        reflexion_threshold: float = 0.3,
        model_router=None,
        reflexion_engine=None,
    ) -> None:
        assert strategy in ("weighted_vote", "highest_confidence"), \
            f"unknown strategy: {strategy}"
        self.strategy = strategy
        self.reflexion_threshold = reflexion_threshold
        self.model_router = model_router
        self.reflexion_engine = reflexion_engine

    def decide(self, organ_results: list[OrganResult], prompt: str = "") -> ExecutiveDecision:
        if not organ_results:
            return ExecutiveDecision(strategy=self.strategy,
                                     final_output="[no organ output]",
                                     confidence=0.0)

        if self.strategy == "highest_confidence":
            decision = self._highest_confidence(organ_results)
        else:
            decision = self._weighted_vote(organ_results)

        # Optionally trigger reflexion on low confidence
        if (self.reflexion_engine is not None
                and decision.confidence < self.reflexion_threshold
                and prompt):
            revised = self.reflexion_engine.reflect_and_revise(
                prompt=prompt, draft=decision.final_output,
                organ_results=organ_results,
            )
            if revised:
                decision.final_output = revised
                decision.reflexion_triggered = True

        return decision

    # -- strategies -----------------------------------------------------------

    def _highest_confidence(self, results: list[OrganResult]) -> ExecutiveDecision:
        best = max(results, key=lambda r: r.confidence)
        return ExecutiveDecision(
            strategy="highest_confidence",
            final_output=str(best.output),
            winning_organs=[best.organ_name],
            tally={best.organ_name: best.confidence},
            confidence=best.confidence,
        )

    def _weighted_vote(self, results: list[OrganResult]) -> ExecutiveDecision:
        tally: dict[str, float] = defaultdict(float)
        contributors: dict[str, list[str]] = defaultdict(list)
        # First, count explicit votes with confidence weighting
        for r in results:
            if r.votes:
                for option, w in r.votes.items():
                    tally[option] += w * max(r.confidence, 0.01)
                    contributors[option].append(r.organ_name)
            else:
                # No explicit vote — use its own output as an implicit vote
                key = _short_key(str(r.output))
                tally[key] += r.confidence
                contributors[key].append(r.organ_name)

        if not tally:
            return self._highest_confidence(results)

        winning_option = max(tally, key=lambda k: tally[k])
        winning_organs = contributors[winning_option]
        total = sum(tally.values()) or 1.0
        winning_conf = tally[winning_option] / total

        # Full text of the highest-confidence contributor to the winning option
        winner_results = [r for r in results if r.organ_name in winning_organs]
        final_text = max(winner_results, key=lambda r: r.confidence).output

        conflicts = []
        if len(tally) > 1:
            for opt, score in tally.items():
                if opt != winning_option and score >= 0.5 * tally[winning_option]:
                    conflicts.append({"option": opt[:80], "score": round(score, 3),
                                      "organs": contributors[opt]})

        return ExecutiveDecision(
            strategy="weighted_vote",
            final_output=str(final_text),
            winning_organs=winning_organs,
            tally={k[:80]: round(v, 3) for k, v in tally.items()},
            confidence=round(winning_conf, 3),
            conflicts=conflicts,
        )


def _short_key(text: str, n: int = 80) -> str:
    return " ".join(text.split())[:n]
