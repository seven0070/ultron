"""
Orchestration strategies.

Each strategy takes (prompt, intent, request_meta) and returns a plan:
  - which models to invoke
  - in what mode (parallel/sequential/cascade)
  - which model aggregates/verifies
  - how to synthesize the final answer

Then MultiModelOrchestrator executes the plan.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Literal

from monad.router.intent import Intent


class ExecutionMode(str, Enum):
    SINGLE = "single"
    PARALLEL = "parallel"
    CASCADE = "cascade"       # try model A; if low confidence, escalate to B


@dataclass
class ExecutionPlan:
    strategy_name: str
    models: list[str]                                # proposers
    mode: ExecutionMode = ExecutionMode.SINGLE
    aggregator: str = ""                              # for MoA / verification
    synth_mode: Literal["best", "aggregate", "vote"] = "best"
    cascade_threshold: float = 0.55                   # score below → escalate
    max_tokens: int = 1024
    temperature: float = 0.7
    top_p: float = 0.9
    metadata: dict = field(default_factory=dict)


class OrchestrationStrategy(ABC):
    name: str = "abstract"

    @abstractmethod
    def plan(self, prompt: str, intent: Intent, model_pool: dict[str, str]) -> ExecutionPlan:
        """
        model_pool maps role -> model_id, e.g. {"reasoning": "longcat2", ...}.
        Returns an ExecutionPlan for the orchestrator to execute.
        """


# ---------------------------------------------------------------------------
# 1. Domain Routing — the cheapest, fastest, most cost-effective pattern
#    (Velsof 2026: "usually outperforms a single frontier model at half the cost")
# ---------------------------------------------------------------------------

class DomainRouting(OrchestrationStrategy):
    name = "domain_routing"

    ROLE_FOR_INTENT: dict[Intent, str] = {
        Intent.CODING: "coding",
        Intent.CREATIVE: "creative",
        Intent.ANALYSIS: "reasoning",
        Intent.SUMMARIZATION: "reasoning",
        Intent.QUESTION: "reasoning",
        Intent.GENERAL_CHAT: "reasoning",
        Intent.UNKNOWN: "reasoning",
    }

    TEMPS_FOR_INTENT: dict[Intent, float] = {
        Intent.CODING: 0.15,        # precision
        Intent.CREATIVE: 0.95,      # variety
        Intent.ANALYSIS: 0.35,
        Intent.SUMMARIZATION: 0.30,
        Intent.QUESTION: 0.55,
        Intent.GENERAL_CHAT: 0.70,
        Intent.UNKNOWN: 0.70,
    }

    def plan(self, prompt, intent, model_pool):
        role = self.ROLE_FOR_INTENT.get(intent, "reasoning")
        model_id = model_pool.get(role) or next(iter(model_pool.values()))
        return ExecutionPlan(
            strategy_name=self.name,
            models=[model_id],
            mode=ExecutionMode.SINGLE,
            synth_mode="best",
            temperature=self.TEMPS_FOR_INTENT.get(intent, 0.7),
            metadata={"role_used": role},
        )


# ---------------------------------------------------------------------------
# 2. Cascade — try cheap/fast first, escalate to strong model on low confidence
# ---------------------------------------------------------------------------

class Cascade(OrchestrationStrategy):
    name = "cascade"

    def __init__(self, threshold: float = 0.55) -> None:
        self.threshold = threshold

    def plan(self, prompt, intent, model_pool):
        # First-line: creative (usually smallest); escalate to reasoning (biggest)
        first = model_pool.get("creative") or model_pool.get("coding")
        escalate = model_pool.get("reasoning")
        chain = [first]
        if escalate and escalate != first:
            chain.append(escalate)
        return ExecutionPlan(
            strategy_name=self.name,
            models=chain,
            mode=ExecutionMode.CASCADE,
            cascade_threshold=self.threshold,
            synth_mode="best",
            temperature=0.6,
        )


# ---------------------------------------------------------------------------
# 3. Mixture-of-Agents — N proposers in parallel + aggregator LLM merges.
#    Best for open-ended reasoning where models complement each other.
# ---------------------------------------------------------------------------

class MixtureOfAgents(OrchestrationStrategy):
    name = "mixture_of_agents"

    def plan(self, prompt, intent, model_pool):
        proposers = list({v for v in model_pool.values() if v})
        aggregator = model_pool.get("reasoning") or proposers[0]
        return ExecutionPlan(
            strategy_name=self.name,
            models=proposers,
            mode=ExecutionMode.PARALLEL,
            aggregator=aggregator,
            synth_mode="aggregate",
            temperature=0.7,
        )


# ---------------------------------------------------------------------------
# 4. Verification — proposer + independent verifier.
#    Best for coding & factual claims (verifier catches proposer's mistakes).
# ---------------------------------------------------------------------------

class Verification(OrchestrationStrategy):
    name = "verification"

    def plan(self, prompt, intent, model_pool):
        proposer = model_pool.get("coding") if intent == Intent.CODING \
                   else model_pool.get("reasoning")
        verifier = model_pool.get("reasoning") if proposer != model_pool.get("reasoning") \
                   else model_pool.get("coding")
        proposer = proposer or next(iter(model_pool.values()))
        verifier = verifier or proposer
        return ExecutionPlan(
            strategy_name=self.name,
            models=[proposer],
            mode=ExecutionMode.SINGLE,
            aggregator=verifier,          # verifier used post-hoc
            synth_mode="aggregate",       # aggregator "rewrites" fixing issues
            temperature=0.25 if intent == Intent.CODING else 0.5,
        )


# ---------------------------------------------------------------------------
# 5. Ensemble — parallel + majority/weighted vote.
#    Best for factual short-answer QA where models should agree.
# ---------------------------------------------------------------------------

class Ensemble(OrchestrationStrategy):
    name = "ensemble"

    def plan(self, prompt, intent, model_pool):
        proposers = list({v for v in model_pool.values() if v})
        return ExecutionPlan(
            strategy_name=self.name,
            models=proposers,
            mode=ExecutionMode.PARALLEL,
            synth_mode="vote",
            temperature=0.3,           # low temp — we want consistent answers
        )


STRATEGY_REGISTRY: dict[str, OrchestrationStrategy] = {
    "domain_routing": DomainRouting(),
    "cascade": Cascade(),
    "mixture_of_agents": MixtureOfAgents(),
    "verification": Verification(),
    "ensemble": Ensemble(),
}
