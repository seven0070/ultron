"""
FusionOrchestrator — top-level entry that produces a single unified answer.

Modes:
    AUTO     Pick the best available mode:
             - LOGITS if tokenizers align & numpy available
             - ENSEMBLE_TOKENS if 2+ models but tokenizers differ
             - CHAIN as universal fallback
    CHAIN    Force sequential draft→refine→polish
    ENSEMBLE Force periodic token voting
    LOGITS   Force logit-level averaging (falls back with reason if unavailable)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from monad.core.logger import get_logger
from monad.orchestration.executor import ParallelExecutor
from monad.orchestration.fusion.aligner import TokenizerAligner, TokenizerCompatibility
from monad.orchestration.fusion.chain import ChainStage, FusionChain
from monad.orchestration.fusion.ensemble_tokens import FusionEnsembleTokens
from monad.orchestration.fusion.logits import FusionLogits

log = get_logger(__name__)


class FusionMode(str, Enum):
    AUTO = "auto"
    CHAIN = "chain"
    ENSEMBLE = "ensemble"
    LOGITS = "logits"


@dataclass
class FusionResult:
    text: str
    mode_used: str
    models_used: list[str] = field(default_factory=list)
    latency_ms: float = 0.0
    fallback_reason: str = ""
    trace: dict = field(default_factory=dict)


class FusionOrchestrator:
    """One call → one unified answer, produced by all loaded models."""

    def __init__(self, inference_manager, model_manager,
                 model_pool: dict[str, str], max_workers: int = 3) -> None:
        self.inference = inference_manager
        self.models = model_manager
        self.model_pool = {k: v for k, v in model_pool.items() if v}
        self.executor = ParallelExecutor(inference_manager, model_manager,
                                          max_workers=max_workers)

    # -- public entry --------------------------------------------------------

    def fuse(self, prompt: str, mode: FusionMode = FusionMode.AUTO,
             max_tokens: int = 1024,
             weights: dict[str, float] | None = None) -> FusionResult:
        model_ids = list(self.model_pool.values())
        if not model_ids:
            return FusionResult(text="[no models configured]", mode_used="none")

        # Ensure all models are loaded (attempt lazy load; skip failures)
        loaded_ids = self._ensure_loaded(model_ids)
        if not loaded_ids:
            return FusionResult(text="[no models could be loaded]",
                                mode_used="none",
                                fallback_reason="no models loadable")

        chosen = self._pick_mode(mode, loaded_ids)
        log.info("Fusion: mode={} models={}", chosen.value, loaded_ids)

        if chosen == FusionMode.CHAIN:
            return self._run_chain(prompt, loaded_ids, max_tokens)
        if chosen == FusionMode.ENSEMBLE:
            return self._run_ensemble(prompt, loaded_ids, max_tokens)
        if chosen == FusionMode.LOGITS:
            return self._run_logits(prompt, loaded_ids, max_tokens, weights)
        return FusionResult(text="[unknown mode]", mode_used=chosen.value)

    # -- mode selection ------------------------------------------------------

    def _pick_mode(self, requested: FusionMode, loaded_ids: list[str]) -> FusionMode:
        if requested != FusionMode.AUTO:
            return requested
        # Try LOGITS first — best fusion when possible
        try:
            provider = self.inference.get_default_provider()
            report = TokenizerAligner(provider).check(loaded_ids)
            if report.compatibility == TokenizerCompatibility.IDENTICAL:
                try:
                    import numpy  # noqa: F401
                    return FusionMode.LOGITS
                except ImportError:
                    log.info("AUTO: numpy missing → falling back from LOGITS")
        except Exception as e:
            log.debug("AUTO: tokenizer probe failed ({}) — skipping LOGITS", e)
        # Ensemble is worthwhile with 2+ models
        if len(loaded_ids) >= 2:
            return FusionMode.ENSEMBLE
        return FusionMode.CHAIN

    # -- runners -------------------------------------------------------------

    def _run_chain(self, prompt: str, model_ids: list[str],
                   max_tokens: int) -> FusionResult:
        # Assign stages by role if pool has roles; else round-robin
        stage_models: dict[ChainStage, str] = {}
        stages = [ChainStage.DRAFT, ChainStage.REFINE, ChainStage.POLISH]
        # Preferred role → stage mapping
        role_to_stage = {"reasoning": ChainStage.DRAFT,
                          "coding": ChainStage.REFINE,
                          "creative": ChainStage.POLISH}
        for role, mid in self.model_pool.items():
            if mid in model_ids and role in role_to_stage:
                stage_models[role_to_stage[role]] = mid
        # Fill any missing stage with round-robin from loaded ids
        rr = iter(model_ids)
        for stage in stages:
            if stage not in stage_models:
                try:
                    stage_models[stage] = next(rr)
                except StopIteration:
                    stage_models[stage] = model_ids[0]

        chain = FusionChain(self.executor, stage_models)
        run = chain.run(prompt, max_tokens=max_tokens)
        return FusionResult(
            text=run.final,
            mode_used="chain",
            models_used=run.models_used,
            latency_ms=round(sum(s.latency_ms for s in run.steps), 1),
            trace={"steps": [
                {"stage": s.stage.value, "model": s.model_id,
                 "chars": len(s.output_text), "latency_ms": s.latency_ms}
                for s in run.steps
            ]},
        )

    def _run_ensemble(self, prompt: str, model_ids: list[str],
                      max_tokens: int) -> FusionResult:
        ens = FusionEnsembleTokens(self.executor, model_ids)
        res = ens.generate(prompt, max_tokens=max_tokens)
        return FusionResult(
            text=res.text,
            mode_used="ensemble",
            models_used=res.models_used,
            latency_ms=res.latency_ms,
            trace={"votes": res.votes_per_step[-5:]},   # last 5 voting rounds
        )

    def _run_logits(self, prompt: str, model_ids: list[str],
                    max_tokens: int, weights: dict[str, float] | None) -> FusionResult:
        provider = self.inference.get_default_provider()
        fuser = FusionLogits(provider, model_ids, weights=weights)
        reason = fuser.available_reason()
        if reason:
            log.info("LOGITS unavailable ({}) — falling back to CHAIN", reason)
            r = self._run_chain(prompt, model_ids, max_tokens)
            r.fallback_reason = f"logits unavailable: {reason}"
            r.mode_used = "chain (logits fallback)"
            return r
        res = fuser.generate(prompt, max_tokens=max_tokens)
        return FusionResult(
            text=res.text,
            mode_used=res.method,
            models_used=res.models_used,
            latency_ms=res.latency_ms,
            fallback_reason=res.fallback_reason,
            trace={"tokens_generated": res.tokens_generated,
                   "weights": fuser.weights},
        )

    # -- helpers -------------------------------------------------------------

    def _ensure_loaded(self, model_ids: list[str]) -> list[str]:
        provider = self.inference.get_default_provider()
        loaded = []
        for mid in model_ids:
            try:
                if not provider.is_loaded(mid):
                    meta = self.models.get(mid)
                    if not meta.local_path:
                        log.debug("skip {} — no local file", mid)
                        continue
                    provider.load_model(meta)
                loaded.append(mid)
            except Exception as e:
                log.warning("cannot load {}: {}", mid, e)
        return loaded
