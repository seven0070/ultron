"""Tests for LLM Fusion — L2/L3/L4 unified-answer strategies."""

from __future__ import annotations

from dataclasses import dataclass
from unittest.mock import MagicMock

import pytest

from monad.orchestration.executor import ProposerResult
from monad.orchestration.fusion import (
    FusionChain, ChainStage,
    FusionEnsembleTokens,
    FusionLogits,
    FusionMode, FusionOrchestrator, FusionResult,
    TokenizerAligner, TokenizerCompatibility,
)


# ---------------------------------------------------------------------------
# Test fixtures — fake provider/executor/manager
# ---------------------------------------------------------------------------

class _FakeProvider:
    """Mimics LlamaCppProvider surface used by fusion."""
    def __init__(self, canned: dict[str, str]) -> None:
        self.canned = canned
        self._loaded: dict[str, object] = {mid: _FakeLlama(mid) for mid in canned}
    def is_loaded(self, mid): return mid in self._loaded
    def load_model(self, meta): self._loaded.setdefault(meta.id, _FakeLlama(meta.id))
    def generate(self, mid, prompt, **kw): return self.canned.get(mid, "(no reply)")


class _FakeLlama:
    def __init__(self, mid): self.mid = mid
    def tokenize(self, text, add_bos=False): return [ord(c) % 256 for c in text.decode("utf-8", errors="ignore")[:32]]
    def detokenize(self, tokens): return bytes(t & 0x7F for t in tokens if t < 128)
    n_vocab = 32000
    def reset(self): pass


class _FakeInferenceManager:
    def __init__(self, provider): self._p = provider
    def get_default_provider(self): return self._p


@dataclass
class _FakeMeta:
    id: str
    local_path: str = "/fake.gguf"


class _FakeModelManager:
    def __init__(self, ids): self._metas = {i: _FakeMeta(i) for i in ids}
    def get(self, mid): return self._metas[mid]


class _FakeExecutor:
    """Minimal executor: returns canned text for run_one/run."""
    def __init__(self, provider): self.provider = provider
    def run_one(self, mid, prompt, **kw):
        text = self.provider.generate(mid, prompt, **kw)
        return ProposerResult(model_id=mid, text=text, latency_ms=10.0)
    def run(self, mids, prompt, **kw):
        return [self.run_one(m, prompt, **kw) for m in mids]


POOL = {"reasoning": "modelA", "coding": "modelB", "creative": "modelC"}


# ---------------------------------------------------------------------------
# TokenizerAligner
# ---------------------------------------------------------------------------

def test_aligner_single_model_trivially_identical():
    prov = _FakeProvider({"a": "x"})
    report = TokenizerAligner(prov).check(["a"])
    assert report.compatibility == TokenizerCompatibility.IDENTICAL


def test_aligner_matching_fake_tokenizers():
    # Two fake llamas produce identical tokens on the same probe strings
    prov = _FakeProvider({"a": "x", "b": "y"})
    report = TokenizerAligner(prov).check(["a", "b"])
    assert report.compatibility == TokenizerCompatibility.IDENTICAL


def test_aligner_unknown_model_returns_different():
    prov = _FakeProvider({"a": "x"})
    report = TokenizerAligner(prov).check(["a", "missing"])
    assert report.compatibility == TokenizerCompatibility.DIFFERENT


# ---------------------------------------------------------------------------
# FusionChain (L2)
# ---------------------------------------------------------------------------

def test_chain_runs_three_stages_in_order():
    prov = _FakeProvider({
        "A": "DRAFT ANSWER",
        "B": "REFINED ANSWER",
        "C": "FINAL ANSWER",
    })
    exec_ = _FakeExecutor(prov)
    chain = FusionChain(
        exec_,
        stage_models={ChainStage.DRAFT: "A",
                      ChainStage.REFINE: "B",
                      ChainStage.POLISH: "C"},
    )
    run = chain.run("What is 2+2?")
    assert len(run.steps) == 3
    assert run.steps[0].stage == ChainStage.DRAFT
    assert run.steps[1].stage == ChainStage.REFINE
    assert run.steps[2].stage == ChainStage.POLISH
    assert run.final == "FINAL ANSWER"
    assert run.models_used == ["A", "B", "C"]


def test_chain_prompts_include_previous_output():
    prov = _FakeProvider({"A": "draft", "B": "refined", "C": "polished"})
    exec_ = _FakeExecutor(prov)
    # Wrap run_one to capture what the refine stage sees
    captured = []
    orig = exec_.run_one
    def spy(mid, prompt, **kw):
        captured.append((mid, prompt))
        return orig(mid, prompt, **kw)
    exec_.run_one = spy

    chain = FusionChain(exec_, stage_models={ChainStage.DRAFT: "A",
                                              ChainStage.REFINE: "B",
                                              ChainStage.POLISH: "C"})
    chain.run("test prompt")

    # The refine prompt should include the draft output
    refine_call = captured[1]
    assert "draft" in refine_call[1]
    # The polish prompt should include the refined output
    polish_call = captured[2]
    assert "refined" in polish_call[1]


def test_chain_skips_stages_without_models():
    prov = _FakeProvider({"A": "just a draft"})
    exec_ = _FakeExecutor(prov)
    chain = FusionChain(exec_, stage_models={ChainStage.DRAFT: "A"})
    run = chain.run("test")
    assert len(run.steps) == 1
    assert run.final == "just a draft"


# ---------------------------------------------------------------------------
# FusionEnsembleTokens (L3)
# ---------------------------------------------------------------------------

def test_ensemble_finds_common_prefix():
    # All three models say the same first few characters, then diverge
    prov = _FakeProvider({
        "A": "The answer is Paris.",
        "B": "The answer is Paris because...",
        "C": "The answer is Paris, capital of France.",
    })
    exec_ = _FakeExecutor(prov)
    ens = FusionEnsembleTokens(exec_, ["A", "B", "C"], chunk_tokens=64)
    result = ens.generate("What is the capital?", max_tokens=100)
    assert "The answer is Paris" in result.text
    assert result.method == "ensemble_tokens"


def test_ensemble_no_consensus_falls_back_to_best():
    prov = _FakeProvider({
        "A": "Xylophone",
        "B": "Yesterday",
        "C": "Zebra",
    })
    exec_ = _FakeExecutor(prov)
    ens = FusionEnsembleTokens(exec_, ["A", "B", "C"], chunk_tokens=64)
    result = ens.generate("test", max_tokens=50)
    # Should produce SOMETHING even without consensus
    assert result.text


# ---------------------------------------------------------------------------
# FusionLogits (L4) — availability + fallback behavior
# ---------------------------------------------------------------------------

def test_logits_available_reason_missing_model():
    prov = _FakeProvider({"A": "x"})
    fuser = FusionLogits(prov, ["A", "missing_model"])
    reason = fuser.available_reason()
    assert "missing_model" in reason


def test_logits_falls_back_gracefully():
    """FusionLogits with a fake provider that lacks .eval_logits should degrade."""
    prov = _FakeProvider({"A": "backup answer", "B": "other"})
    fuser = FusionLogits(prov, ["A", "B"])
    # Fake llama doesn't produce real logits — should either report unavailable
    # or fall back to single-model
    result = fuser.generate("test", max_tokens=20)
    assert result.method in ("unavailable", "fallback_single", "logits_fusion")


# ---------------------------------------------------------------------------
# FusionOrchestrator — top-level integration
# ---------------------------------------------------------------------------

def test_orchestrator_auto_picks_something(monkeypatch):
    prov = _FakeProvider({"modelA": "reasoning draft",
                          "modelB": "coding refine",
                          "modelC": "creative polish"})
    im = _FakeInferenceManager(prov)
    mm = _FakeModelManager(list(prov.canned))
    fuser = FusionOrchestrator(im, mm, POOL)
    # Monkey-patch numpy import inside logits pick to force fallback
    result = fuser.fuse("test", mode=FusionMode.CHAIN, max_tokens=100)
    assert result.text
    assert result.mode_used == "chain"
    assert set(result.models_used) == {"modelA", "modelB", "modelC"}


def test_orchestrator_chain_mode_produces_single_answer():
    prov = _FakeProvider({"modelA": "Draft: 2+2=4",
                          "modelB": "Refined: 2+2 equals 4",
                          "modelC": "The answer is 4."})
    im = _FakeInferenceManager(prov)
    mm = _FakeModelManager(list(prov.canned))
    fuser = FusionOrchestrator(im, mm, POOL)
    result = fuser.fuse("what is 2+2?", mode=FusionMode.CHAIN)
    assert result.mode_used == "chain"
    assert result.text == "The answer is 4."
    assert result.trace["steps"][0]["stage"] == "draft"
    assert result.trace["steps"][-1]["stage"] == "polish"


def test_orchestrator_ensemble_mode():
    prov = _FakeProvider({"modelA": "Common start diverging A",
                          "modelB": "Common start diverging B",
                          "modelC": "Common start diverging C"})
    im = _FakeInferenceManager(prov)
    mm = _FakeModelManager(list(prov.canned))
    fuser = FusionOrchestrator(im, mm, POOL)
    result = fuser.fuse("test", mode=FusionMode.ENSEMBLE, max_tokens=100)
    assert result.mode_used == "ensemble"
    assert "Common start" in result.text


def test_orchestrator_logits_falls_back_to_chain_when_unavailable():
    prov = _FakeProvider({"modelA": "a", "modelB": "b", "modelC": "c"})
    im = _FakeInferenceManager(prov)
    mm = _FakeModelManager(list(prov.canned))
    fuser = FusionOrchestrator(im, mm, POOL)
    result = fuser.fuse("test", mode=FusionMode.LOGITS)
    # Either succeeds with logits (unlikely with fake) OR falls back to chain
    assert result.mode_used in ("logits_fusion", "chain (logits fallback)",
                                 "fallback_single")


def test_orchestrator_empty_pool_returns_error():
    prov = _FakeProvider({})
    im = _FakeInferenceManager(prov)
    mm = _FakeModelManager([])
    fuser = FusionOrchestrator(im, mm, {})
    result = fuser.fuse("test")
    assert "no models" in result.text.lower()
