"""
ModelRouter — routes a task to the right model tier.

Two APIs coexist:
  1. `route(prompt)` → generic complexity-based routing (Monad-Ultron style)
  2. `select(task, complexity)` + `select_for_organ(organ_name, complexity)`
     — Cognitive Architecture spec API with concrete model IDs

Tiers:
    LOCAL_FAST       — Mistral Small 3 7B (Ollama)
    LOCAL_STRONG     — DeepSeek R1 8B (Ollama)
    CLOUD_CHEAP      — Claude Haiku 3.5  (opt-in via ANTHROPIC_API_KEY)
    CLOUD_FRONTIER   — Claude Opus 4     (opt-in via ANTHROPIC_API_KEY)

Cloud tiers are only used when a key is present, unless `prefer_local=True`.
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
    TRIVIAL = "trivial"
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    FRONTIER = "frontier"
    CODE = "code"          # from user spec
    SENSITIVE = "sensitive"    # from user spec — forces local


@dataclass
class ModelConfig:
    """Concrete model identity (matches user spec)."""
    name: str
    tier: ModelTier
    provider: str
    model_id: str
    cost_per_1k_tokens: float
    max_tokens: int


# Concrete model registry — names/IDs from user's Cognitive Architecture spec.
MODELS: dict[str, ModelConfig] = {
    "mistral-small": ModelConfig(
        "Mistral Small 3 7B", ModelTier.LOCAL_FAST,
        "ollama", "mistral-small3", 0.0, 32768,
    ),
    "deepseek-r1": ModelConfig(
        "DeepSeek R1 8B", ModelTier.LOCAL_STRONG,
        "ollama", "deepseek-r1:8b", 0.0, 32768,
    ),
    "claude-haiku": ModelConfig(
        "Claude Haiku 3.5", ModelTier.CLOUD_CHEAP,
        "anthropic", "claude-3-5-haiku-20241022", 0.00025, 8192,
    ),
    "claude-opus": ModelConfig(
        "Claude Opus 4", ModelTier.CLOUD_FRONTIER,
        "anthropic", "claude-opus-4-20250514", 0.015, 32768,
    ),
}


@dataclass
class RoutingDecision:
    tier: ModelTier
    model_id: str
    reason: str


# Organs that are "high stakes" — earn a stronger model when confidence is high
HIGH_STAKES_ORGANS = {
    "Ruin Detector", "Collective Mind", "Entropy Pulse",
    "Sensitivity Awareness",
}


class ModelRouter:
    """
    prefer_local=True forces every route to LOCAL_FAST regardless of task.
    """

    _TRIVIAL_RE = re.compile(r"^\s*(yes|no|ok|hi|hello|thanks?)\b", re.IGNORECASE)
    _FRONTIER_RE = re.compile(
        r"\b(design|architect|research|novel|from scratch|prove|derive|"
        r"comprehensive|end-to-end|long-form)\b", re.IGNORECASE,
    )
    _COMPLEX_RE = re.compile(
        r"\b(code|function|class|debug|refactor|analyze|compare|plan|"
        r"algorithm|implement|optimi[sz]e)\b", re.IGNORECASE,
    )
    _MODERATE_RE = re.compile(
        r"\b(explain|summari[sz]e|list|walk me through|how does)\b", re.IGNORECASE,
    )

    def __init__(
        self,
        prefer_local: bool = False,
        tier_to_model_key: dict[ModelTier, str] | None = None,
    ) -> None:
        self.prefer_local = prefer_local
        self.tier_to_key = tier_to_model_key or {
            ModelTier.LOCAL_FAST: "mistral-small",
            ModelTier.LOCAL_STRONG: "deepseek-r1",
            ModelTier.CLOUD_CHEAP: "claude-haiku",
            ModelTier.CLOUD_FRONTIER: "claude-opus",
        }

    # -- capability checks ---------------------------------------------------

    def cloud_available(self) -> bool:
        if self.prefer_local:
            return False
        return bool(os.environ.get("ANTHROPIC_API_KEY")
                    or os.environ.get("OPENAI_API_KEY"))

    def frontier_available(self) -> bool:
        return self.cloud_available()

    # -- spec API: select(task, complexity) → ModelConfig --------------------

    def select(self, task: str, complexity: TaskComplexity) -> ModelConfig:
        """From user's Cognitive Architecture spec.

        Rules:
          SENSITIVE or prefer_local  → mistral-small (LOCAL_FAST)
          SIMPLE / TRIVIAL          → mistral-small
          CODE                       → deepseek-r1 (LOCAL_STRONG)
          MODERATE                   → claude-haiku (CLOUD_CHEAP) or local fallback
          COMPLEX / FRONTIER         → claude-opus (CLOUD_FRONTIER) or local fallback
        """
        if complexity == TaskComplexity.SENSITIVE or self.prefer_local:
            return MODELS["mistral-small"]
        if complexity in (TaskComplexity.SIMPLE, TaskComplexity.TRIVIAL):
            return MODELS["mistral-small"]
        if complexity == TaskComplexity.CODE:
            return MODELS["deepseek-r1"]
        if complexity == TaskComplexity.MODERATE:
            return MODELS["claude-haiku"] if self.cloud_available() else MODELS["deepseek-r1"]
        # COMPLEX or FRONTIER
        if self.frontier_available():
            return MODELS["claude-opus"]
        return MODELS["deepseek-r1"]

    def select_for_organ(self, organ_name: str, complexity: float) -> ModelConfig:
        """Per-organ selection.

        High-stakes organs get frontier models when complexity is high, cheap
        cloud otherwise. Everyone else stays local.
        """
        if organ_name in HIGH_STAKES_ORGANS and complexity > 0.7:
            return MODELS["claude-opus"] if self.frontier_available() else MODELS["deepseek-r1"]
        if organ_name in HIGH_STAKES_ORGANS:
            return MODELS["claude-haiku"] if self.cloud_available() else MODELS["deepseek-r1"]
        return MODELS["mistral-small"]

    # -- generic prompt-based routing (Monad-Ultron original API) ------------

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

    def route(self, prompt: str, force_tier: ModelTier | None = None) -> RoutingDecision:
        if force_tier is not None:
            return RoutingDecision(
                tier=force_tier,
                model_id=MODELS[self.tier_to_key[force_tier]].model_id,
                reason=f"forced tier: {force_tier.value}",
            )
        complexity = self.classify(prompt)
        model = self.select(prompt, complexity)
        return RoutingDecision(
            tier=model.tier, model_id=model.model_id,
            reason=f"complexity={complexity.value} → {model.name}",
        )
