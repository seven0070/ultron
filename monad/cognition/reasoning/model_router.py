"""
ModelRouter — routes a task to the right model tier.

Tiers:
    LOCAL_FAST       — small local model (Llama 3.2 3B / draft)
    LOCAL_STRONG     — big local model (Qwen 2.5 7B / DeepSeek)
    CLOUD_CHEAP      — cloud small (Claude Haiku / GPT-4o mini) [opt-in via env]
    CLOUD_FRONTIER   — cloud strong (Claude Opus / GPT-4o) [opt-in via env]

The USER selected "opt-in cloud via env var" — cloud tiers are only offered
when ANTHROPIC_API_KEY or OPENAI_API_KEY is present. Otherwise the router
transparently falls back to LOCAL_STRONG.

TaskComplexity thresholds:
    TRIVIAL   → LOCAL_FAST
    SIMPLE    → LOCAL_FAST (or LOCAL_STRONG if unavailable)
    MODERATE  → LOCAL_STRONG
    COMPLEX   → CLOUD_CHEAP if available, else LOCAL_STRONG
    FRONTIER  → CLOUD_FRONTIER if available, else LOCAL_STRONG
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from enum import Enum


class ModelTier(str, Enum):
    LOCAL_FAST = "local_fast"
    LOCAL_STRONG = "local_strong"
    CLOUD_CHEAP = "cloud_cheap"
    CLOUD_FRONTIER = "cloud_frontier"


class TaskComplexity(str, Enum):
    TRIVIAL = "trivial"       # yes/no, format, echo
    SIMPLE = "simple"         # short factual, summarize small text
    MODERATE = "moderate"     # multi-step reasoning
    COMPLEX = "complex"       # code gen, analysis, planning
    FRONTIER = "frontier"     # research, novel synthesis


DEFAULT_MODEL_FOR_TIER: dict[ModelTier, str] = {
    ModelTier.LOCAL_FAST: "llama2",              # Llama 3.2 3B in our models.yaml
    ModelTier.LOCAL_STRONG: "longcat2",          # Qwen 2.5 7B in our models.yaml
    ModelTier.CLOUD_CHEAP: "claude-haiku",       # informational — actual call in adapter
    ModelTier.CLOUD_FRONTIER: "claude-opus",
}


@dataclass
class RoutingDecision:
    tier: ModelTier
    model_id: str
    reason: str


class ModelRouter:
    """Cheap heuristic router — no model calls, no network."""

    # Signal words
    _TRIVIAL_RE = re.compile(r"^\s*(yes|no|ok|hi|hello|thanks?)\b", re.IGNORECASE)
    _FRONTIER_RE = re.compile(
        r"\b(design|architect|research|novel|from scratch|prove|derive|"
        r"comprehensive|end-to-end|long-form)\b",
        re.IGNORECASE,
    )
    _COMPLEX_RE = re.compile(
        r"\b(code|function|class|debug|refactor|analyze|compare|plan|"
        r"algorithm|implement|optimi[sz]e)\b",
        re.IGNORECASE,
    )
    _MODERATE_RE = re.compile(
        r"\b(explain|summari[sz]e|list|walk me through|how does)\b",
        re.IGNORECASE,
    )

    def __init__(self, tier_to_model: dict[ModelTier, str] | None = None) -> None:
        self.tier_to_model = tier_to_model or dict(DEFAULT_MODEL_FOR_TIER)

    # -- capability detection -------------------------------------------------

    def cloud_available(self) -> bool:
        return bool(os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("OPENAI_API_KEY"))

    def frontier_available(self) -> bool:
        return self.cloud_available()

    # -- classification -------------------------------------------------------

    def classify(self, prompt: str) -> TaskComplexity:
        p = prompt.strip()
        if not p or self._TRIVIAL_RE.match(p) or len(p) < 12:
            return TaskComplexity.TRIVIAL
        if self._FRONTIER_RE.search(p) or len(p) > 800:
            return TaskComplexity.FRONTIER
        if self._COMPLEX_RE.search(p):
            return TaskComplexity.COMPLEX
        if self._MODERATE_RE.search(p) or len(p) > 200:
            return TaskComplexity.MODERATE
        return TaskComplexity.SIMPLE

    # -- routing --------------------------------------------------------------

    def route(self, prompt: str, force_tier: ModelTier | None = None) -> RoutingDecision:
        if force_tier is not None:
            return RoutingDecision(
                tier=force_tier,
                model_id=self.tier_to_model[force_tier],
                reason=f"forced tier: {force_tier.value}",
            )

        complexity = self.classify(prompt)
        cloud_ok = self.cloud_available()

        if complexity in (TaskComplexity.TRIVIAL, TaskComplexity.SIMPLE):
            tier = ModelTier.LOCAL_FAST
            reason = f"complexity={complexity.value} → local fast"
        elif complexity == TaskComplexity.MODERATE:
            tier = ModelTier.LOCAL_STRONG
            reason = f"complexity={complexity.value} → local strong"
        elif complexity == TaskComplexity.COMPLEX:
            tier = ModelTier.CLOUD_CHEAP if cloud_ok else ModelTier.LOCAL_STRONG
            reason = (f"complexity={complexity.value} → cloud cheap" if cloud_ok
                      else f"complexity={complexity.value} → local strong (no cloud key)")
        else:  # FRONTIER
            tier = ModelTier.CLOUD_FRONTIER if cloud_ok else ModelTier.LOCAL_STRONG
            reason = (f"complexity={complexity.value} → cloud frontier" if cloud_ok
                      else f"complexity={complexity.value} → local strong (no cloud key)")

        return RoutingDecision(
            tier=tier, model_id=self.tier_to_model[tier], reason=reason,
        )
