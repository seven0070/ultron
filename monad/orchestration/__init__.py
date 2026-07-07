"""
Build #017 — Multi-model orchestration.

Coordinates LongCat / GLM / Llama (or any registered models) using battle-tested
patterns from the 2026 multi-LLM orchestration literature:

  1. DomainRouting     — classify → route to specialist (cheapest, fastest)
  2. Cascade           — cheap model first; escalate on low confidence
  3. MixtureOfAgents   — N proposers → aggregator LLM merges
  4. Verification      — proposer + independent verifier
  5. Ensemble          — parallel + majority/weighted vote (best for factual QA)

Strategy is chosen per-request by IntentClassifier + config, so different
question types automatically get the right treatment.

Design references:
  - Velsof "Multi-LLM Orchestration in 2026: 7 Battle-Tested Patterns"
  - SLM-MUX (ICLR 2026): discussion-based orchestration FAILS for small models
    → we default to selection-based routing, not debate.
"""

from monad.orchestration.confidence import ConfidenceScorer
from monad.orchestration.executor import ParallelExecutor, ProposerResult
from monad.orchestration.synthesizer import ResponseSynthesizer
from monad.orchestration.orchestrator import MultiModelOrchestrator
from monad.orchestration.strategies import (
    OrchestrationStrategy,
    DomainRouting,
    Cascade,
    MixtureOfAgents,
    Verification,
    Ensemble,
    STRATEGY_REGISTRY,
)

__all__ = [
    "ConfidenceScorer",
    "ParallelExecutor", "ProposerResult",
    "ResponseSynthesizer",
    "MultiModelOrchestrator",
    "OrchestrationStrategy",
    "DomainRouting", "Cascade", "MixtureOfAgents", "Verification", "Ensemble",
    "STRATEGY_REGISTRY",
]
