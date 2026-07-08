"""
MultiModelOrchestrator — the top-level "brain" that runs a request through
the chosen strategy.

Flow:
    prompt
      ↓
    IntentClassifier         (from monad.router)
      ↓
    OrchestrationStrategy    (chosen by config or auto)
      ↓
    ExecutionPlan            (which models, what mode)
      ↓
    ParallelExecutor         (runs proposers)
      ↓  (if CASCADE and low confidence)
    Escalate                 (rerun on stronger model)
      ↓
    ResponseSynthesizer      (best / vote / aggregate)
      ↓
    Response
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from monad.core.logger import get_logger
from monad.orchestration.confidence import ConfidenceScorer
from monad.orchestration.executor import ParallelExecutor, ProposerResult
from monad.orchestration.strategies import (
    ExecutionMode, ExecutionPlan, OrchestrationStrategy, STRATEGY_REGISTRY,
)
from monad.orchestration.synthesizer import ResponseSynthesizer, SynthesisResult
from monad.router.classifier import IntentClassifier
from monad.router.intent import Intent
from monad.router.request import Request, Response

log = get_logger(__name__)


AUTO_STRATEGY_FOR_INTENT: dict[Intent, str] = {
    Intent.CODING: "verification",           # code needs a second pair of eyes
    Intent.CREATIVE: "domain_routing",       # single creative model = variety
    Intent.ANALYSIS: "mixture_of_agents",    # analysis benefits from multiple views
    Intent.SUMMARIZATION: "domain_routing",  # summarization is well-solved
    Intent.QUESTION: "cascade",              # try cheap, escalate if unsure
    Intent.GENERAL_CHAT: "domain_routing",   # keep chat fast
    Intent.UNKNOWN: "cascade",
}


@dataclass
class OrchestrationTrace:
    """Full record of how a response was produced — used for the CLI and audit."""
    strategy: str
    intent: str
    models_invoked: list[str] = field(default_factory=list)
    proposer_results: list[dict] = field(default_factory=list)
    synthesis_mode: str = ""
    final_model: str = ""
    total_latency_ms: float = 0.0
    escalated: bool = False


class MultiModelOrchestrator:
    def __init__(
        self,
        inference_manager,
        model_manager,
        model_pool: dict[str, str],
        default_strategy: str = "auto",
        max_workers: int = 3,
        cache=None,                        # Optional ResponseCache (Build #024)
        adaptive_router=None,              # Optional AdaptiveRouter (Build #020)
    ) -> None:
        """
        model_pool: {"reasoning": "longcat2", "coding": "glm5", "creative": "llama3"}
        default_strategy: name from STRATEGY_REGISTRY, or "auto" for per-intent selection.
        cache: optional ResponseCache — bypasses the LLM on repeat prompts.
        adaptive_router: optional AdaptiveRouter — replaces the static AUTO map
                         with learned per-intent strategy selection.
        """
        self.classifier = IntentClassifier()
        self.executor = ParallelExecutor(inference_manager, model_manager, max_workers=max_workers)
        self.synthesizer = ResponseSynthesizer(self.executor)
        self.scorer = ConfidenceScorer()
        self.model_pool = {k: v for k, v in model_pool.items() if v}
        self.default_strategy = default_strategy
        self.cache = cache
        self.adaptive_router = adaptive_router

    # -- public API -----------------------------------------------------------

    def handle(self, request: Request, strategy_override: str = "") -> tuple[Response, OrchestrationTrace]:
        t0 = time.perf_counter()
        self._last_prompt = request.text          # used by cascade/single helpers

        # Cache check FIRST — skip everything if we have a hit (Build #024)
        cache_key = None
        if self.cache is not None:
            cache_key = self.cache.make_key(
                self.default_strategy, request.text,
                strategy_override=strategy_override,
            )
            hit = self.cache.get(cache_key)
            if hit is not None:
                trace = OrchestrationTrace(
                    strategy=strategy_override or "cache",
                    intent="cached",
                    models_invoked=[hit.model_id],
                    proposer_results=[],
                    synthesis_mode="cache",
                    final_model=hit.model_id,
                    total_latency_ms=round((time.perf_counter() - t0) * 1000, 1),
                    escalated=False,
                )
                resp = Response(
                    text=hit.text, intent=Intent.UNKNOWN, model_id=hit.model_id,
                    tokens=hit.tokens, latency_ms=hit.latency_ms,
                    metadata={"strategy": "cache", "cache_hits": hit.hit_count,
                              "trace": trace.__dict__},
                )
                return resp, trace

        # Optional cognition pre-pass — adds memory hits + organ hints to the prompt
        cognition_enrichment = self._cognition_enrich(request.text)

        intent = self.classifier.classify(request.text)
        strat_name = strategy_override or self._select_strategy(intent)
        strategy = STRATEGY_REGISTRY.get(strat_name)
        if strategy is None:
            raise ValueError(f"Unknown strategy: {strat_name}")

        plan = strategy.plan(request.text, intent, self.model_pool)
        log.info("Orchestrate: intent={} strategy={} models={} mode={}",
                 intent.value, strat_name, plan.models, plan.mode.value)

        trace = OrchestrationTrace(
            strategy=strat_name, intent=intent.value,
            models_invoked=plan.models[:],
        )

        # Enriched prompt = original + cognition context
        prompt = request.text
        if cognition_enrichment:
            prompt = cognition_enrichment + "\n\n" + prompt
            trace.metadata = trace.metadata if hasattr(trace, "metadata") else {}

        # Execute
        if plan.mode == ExecutionMode.SINGLE:
            results = [self._run_single(plan, prompt)]
        elif plan.mode == ExecutionMode.PARALLEL:
            results = self._run_parallel(plan, prompt)
        elif plan.mode == ExecutionMode.CASCADE:
            results, escalated = self._run_cascade(plan, prompt)
            trace.escalated = escalated
        else:
            raise ValueError(f"Unknown execution mode: {plan.mode}")

        trace.proposer_results = [
            {"model": r.model_id, "latency_ms": r.latency_ms,
             "confidence": r.confidence.score if r.confidence else None,
             "ok": r.ok, "error": r.error}
            for r in results
        ]

        # Synthesize
        synth = self.synthesizer.synthesize(
            results,
            mode=plan.synth_mode,
            aggregator_model=plan.aggregator,
            original_prompt=request.text,
        )
        trace.synthesis_mode = synth.mode
        trace.final_model = synth.picked_model or synth.aggregator_model
        trace.total_latency_ms = round((time.perf_counter() - t0) * 1000, 1)

        response = Response(
            text=synth.text,
            intent=intent,
            model_id=trace.final_model,
            tokens=len(synth.text.split()),
            latency_ms=trace.total_latency_ms,
            metadata={"strategy": strat_name, "trace": trace.__dict__},
        )

        # Cache the result (Build #024)
        if self.cache is not None and cache_key is not None and synth.text:
            from monad.orchestration.cache import CacheEntry
            self.cache.put(CacheEntry(
                key=cache_key, text=synth.text,
                model_id=trace.final_model, tokens=response.tokens,
                latency_ms=trace.total_latency_ms,
                metadata={"strategy": strat_name, "intent": intent.value},
            ))

        # Record outcome for adaptive routing (Build #020)
        if self.adaptive_router is not None:
            # "Success" = non-empty response AND (either no confidence data OR reasonable score)
            confs = [pr for pr in trace.proposer_results if pr.get("confidence") is not None]
            avg_conf = sum(pr["confidence"] for pr in confs) / len(confs) if confs else 0.7
            success = bool(synth.text.strip()) and avg_conf >= 0.4
            self.adaptive_router.record(
                intent=intent.value, strategy=strat_name,
                success=success, latency_ms=trace.total_latency_ms,
                confidence=avg_conf,
            )

        return response, trace

    # -- execution helpers ----------------------------------------------------

    def _run_single(self, plan: ExecutionPlan, prompt: str) -> ProposerResult:
        return self.executor.run_one(
            plan.models[0], prompt,
            max_tokens=plan.max_tokens, temperature=plan.temperature,
            top_p=plan.top_p, scorer=self.scorer,
        )

    def _run_parallel(self, plan: ExecutionPlan, prompt: str) -> list[ProposerResult]:
        return self.executor.run(
            plan.models, prompt,
            max_tokens=plan.max_tokens, temperature=plan.temperature,
            top_p=plan.top_p, scorer=self.scorer,
        )

    def _run_cascade(self, plan: ExecutionPlan, prompt: str) -> tuple[list[ProposerResult], bool]:
        results: list[ProposerResult] = []
        escalated = False
        for i, mid in enumerate(plan.models):
            r = self.executor.run_one(
                mid, prompt,
                max_tokens=plan.max_tokens, temperature=plan.temperature,
                top_p=plan.top_p, scorer=self.scorer,
            )
            results.append(r)
            conf = r.confidence.score if r.confidence else 0.0
            if r.ok and conf >= plan.cascade_threshold:
                log.debug("Cascade: {} passed threshold ({:.2f} >= {:.2f})",
                          mid, conf, plan.cascade_threshold)
                break
            if i < len(plan.models) - 1:
                log.info("Cascade: escalating from {} (conf={:.2f}) to {}",
                         mid, conf, plan.models[i + 1])
                escalated = True
        return results, escalated

    # -- strategy selection ---------------------------------------------------

    def _select_strategy(self, intent: Intent) -> str:
        if self.default_strategy != "auto":
            return self.default_strategy
        # Adaptive first, static map as fallback (Build #020)
        if self.adaptive_router is not None:
            return self.adaptive_router.select(
                intent=intent.value,
                allowed=list(STRATEGY_REGISTRY.keys()),
                default=AUTO_STRATEGY_FOR_INTENT.get(intent, "domain_routing"),
            )
        return AUTO_STRATEGY_FOR_INTENT.get(intent, "domain_routing")

    # -- misc -----------------------------------------------------------------

    def handle_text(self, text: str, strategy_override: str = "") -> tuple[Response, OrchestrationTrace]:
        """Convenience wrapper for callers that only have a raw string."""
        return self.handle(Request(text=text), strategy_override=strategy_override)

    # -- optional cognition pre-pass -----------------------------------------

    def attach_cognition(self, cognitive_monad) -> None:
        """Wire a `monad.cognition.Monad` instance in as a pre-pass."""
        self._cognition = cognitive_monad

    def _cognition_enrich(self, prompt: str) -> str:
        """If cognition is attached, run .think() and produce a compact context header."""
        cog = getattr(self, "_cognition", None)
        if cog is None:
            return ""
        try:
            cycle = cog.think(prompt)
        except Exception as e:
            log.debug("cognition pre-pass failed: {}", e)
            return ""
        parts = []
        if cycle.memory_hits:
            parts.append("[relevant memory]")
            for h in cycle.memory_hits[:3]:
                text = h.get("text", "") if isinstance(h, dict) else str(h)
                parts.append(f"  - {text[:150]}")
        if cycle.activated_organs:
            parts.append(f"[cognitive lenses: {', '.join(cycle.activated_organs[:6])}]")
        if cycle.decision and cycle.decision.get("winning_organs"):
            parts.append(f"[executive suggests: {', '.join(cycle.decision['winning_organs'])}]")
        return "\n".join(parts) if parts else ""
