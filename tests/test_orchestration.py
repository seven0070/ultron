"""Tests for Build #017 — Multi-Model Orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from unittest.mock import MagicMock

import pytest

from monad.orchestration.confidence import ConfidenceScorer
from monad.orchestration.executor import ProposerResult
from monad.orchestration.orchestrator import MultiModelOrchestrator
from monad.orchestration.strategies import (
    Cascade, DomainRouting, Ensemble, ExecutionMode,
    MixtureOfAgents, STRATEGY_REGISTRY, Verification,
)
from monad.orchestration.synthesizer import ResponseSynthesizer
from monad.router.intent import Intent


# ---------------------------------------------------------------------------
# ConfidenceScorer
# ---------------------------------------------------------------------------

def test_confidence_full_answer_scores_high():
    s = ConfidenceScorer()
    text = ("The capital of France is Paris. It has been the political and cultural "
            "center of the country for centuries and hosts landmarks like the Eiffel "
            "Tower and the Louvre.")
    report = s.score(text)
    assert report.score > 0.85
    assert report.length_ok
    assert report.no_hedging
    assert report.no_refusal


def test_confidence_hedging_penalized():
    s = ConfidenceScorer()
    r = s.score("I'm not sure but maybe it's Paris or London.")
    assert r.no_hedging is False
    assert r.score < 0.8


def test_confidence_refusal_penalized():
    s = ConfidenceScorer()
    r = s.score("I cannot help with that request.")
    assert r.no_refusal is False


def test_confidence_repetition_penalized():
    s = ConfidenceScorer()
    text = ("The cat sat on the mat. " * 20).strip()
    r = s.score(text)
    assert r.low_repetition is False


def test_confidence_unclosed_fence_penalized():
    s = ConfidenceScorer()
    r = s.score("Here is the code:\n```python\ndef foo():\n    return 1\n")
    assert r.complete_format is False


# ---------------------------------------------------------------------------
# Strategies produce sane plans
# ---------------------------------------------------------------------------

POOL = {"reasoning": "longcat2", "coding": "glm5", "creative": "llama2"}


def test_domain_routing_picks_role():
    plan = DomainRouting().plan("write code", Intent.CODING, POOL)
    assert plan.models == ["glm5"]
    assert plan.mode == ExecutionMode.SINGLE
    assert plan.temperature < 0.3        # coding = low temp


def test_cascade_lists_two_models():
    plan = Cascade().plan("what is 2+2", Intent.QUESTION, POOL)
    assert plan.mode == ExecutionMode.CASCADE
    assert len(plan.models) == 2
    assert plan.models[0] != plan.models[1]


def test_mixture_of_agents_parallel_with_aggregator():
    plan = MixtureOfAgents().plan("analyze this", Intent.ANALYSIS, POOL)
    assert plan.mode == ExecutionMode.PARALLEL
    assert set(plan.models) == set(POOL.values())
    assert plan.aggregator in POOL.values()
    assert plan.synth_mode == "aggregate"


def test_verification_has_aggregator():
    plan = Verification().plan("write a fn", Intent.CODING, POOL)
    assert plan.aggregator
    assert plan.aggregator != plan.models[0]


def test_ensemble_uses_vote():
    plan = Ensemble().plan("who wrote Hamlet", Intent.QUESTION, POOL)
    assert plan.synth_mode == "vote"
    assert plan.mode == ExecutionMode.PARALLEL


def test_registry_has_all_strategies():
    for name in ("domain_routing", "cascade", "mixture_of_agents",
                 "verification", "ensemble"):
        assert name in STRATEGY_REGISTRY


# ---------------------------------------------------------------------------
# Synthesizer
# ---------------------------------------------------------------------------

def _make_result(mid: str, text: str, score: float = 0.8, ok: bool = True):
    from monad.orchestration.confidence import ConfidenceReport
    r = ProposerResult(model_id=mid, text=text if ok else "", latency_ms=100.0)
    if not ok:
        r.error = "boom"
    r.confidence = ConfidenceReport(
        score=score, length_ok=True, no_hedging=True, no_refusal=True,
        low_repetition=True, complete_format=True, reasons=[],
    )
    return r


def test_synthesizer_best_picks_highest_confidence():
    synth = ResponseSynthesizer(executor=MagicMock())
    results = [
        _make_result("a", "short answer", score=0.5),
        _make_result("b", "much better answer", score=0.9),
        _make_result("c", "meh", score=0.7),
    ]
    out = synth.synthesize(results, mode="best")
    assert out.picked_model == "b"
    assert "better" in out.text


def test_synthesizer_vote_picks_majority():
    synth = ResponseSynthesizer(executor=MagicMock())
    results = [
        _make_result("a", "The answer is Paris.", score=0.7),
        _make_result("b", "The answer is Paris.", score=0.8),
        _make_result("c", "The answer is London.", score=0.9),
    ]
    out = synth.synthesize(results, mode="vote")
    assert "Paris" in out.text
    assert out.mode == "vote"


def test_synthesizer_all_failed_returns_error():
    synth = ResponseSynthesizer(executor=MagicMock())
    results = [_make_result("a", "", ok=False), _make_result("b", "", ok=False)]
    out = synth.synthesize(results, mode="best")
    assert "all proposers failed" in out.text


# ---------------------------------------------------------------------------
# Full orchestrator (with mocked inference)
# ---------------------------------------------------------------------------

class _FakeProvider:
    def __init__(self, canned: dict[str, str]) -> None:
        self.canned = canned
        self.loaded = set(canned)
    def is_loaded(self, mid): return mid in self.loaded
    def load_model(self, meta): self.loaded.add(meta.id)
    def generate(self, mid, prompt, **kw): return self.canned.get(mid, "(no reply)")


class _FakeInferenceManager:
    def __init__(self, provider): self._p = provider
    def get_default_provider(self): return self._p


@dataclass
class _FakeMeta:
    id: str
    local_path: str = "/fake/path.gguf"


class _FakeModelManager:
    def __init__(self, ids): self._metas = {i: _FakeMeta(i) for i in ids}
    def get(self, mid): return self._metas[mid]


def test_orchestrator_domain_routing_single_call():
    prov = _FakeProvider({
        "longcat2": "reasoning answer",
        "glm5": "def foo():\n    return 42\n",
        "llama2": "creative burst",
    })
    orch = MultiModelOrchestrator(
        inference_manager=_FakeInferenceManager(prov),
        model_manager=_FakeModelManager(list(prov.canned)),
        model_pool=POOL,
        default_strategy="domain_routing",
    )
    resp, trace = orch.handle_text("Hello there")
    assert resp.text
    assert trace.strategy == "domain_routing"
    assert len(trace.models_invoked) == 1


def test_orchestrator_auto_selects_verification_for_code():
    prov = _FakeProvider({
        "longcat2": "reasoning",
        "glm5": "def add(a, b):\n    return a + b\n",
        "llama2": "creative",
    })
    orch = MultiModelOrchestrator(
        inference_manager=_FakeInferenceManager(prov),
        model_manager=_FakeModelManager(list(prov.canned)),
        model_pool=POOL,
        default_strategy="auto",
    )
    resp, trace = orch.handle_text("write a python function to add two numbers")
    assert trace.intent == "coding"
    assert trace.strategy == "verification"


def test_orchestrator_cascade_escalates_on_low_confidence():
    prov = _FakeProvider({
        "longcat2": "This is a full, well-formed reasoning answer with enough length "
                    "to comfortably pass the confidence scorer thresholds.",
        # Multiple failure signals → score well below 0.55 threshold:
        #   hedge + refusal + unclosed code fence
        "llama2": "I don't know. I cannot help with that. ```python\ndef x():",
    })
    orch = MultiModelOrchestrator(
        inference_manager=_FakeInferenceManager(prov),
        model_manager=_FakeModelManager(list(prov.canned)),
        model_pool=POOL,
        default_strategy="cascade",
    )
    resp, trace = orch.handle_text("What is the meaning of life?")
    assert trace.escalated is True
    assert len(trace.proposer_results) == 2
