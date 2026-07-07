"""Tests for the Monad Cognitive Architecture."""

from __future__ import annotations

import pytest

from monad.cognition import Monad, MonadConfig, OrganCategory, register_all
from monad.cognition.executive import ExecutiveController
from monad.cognition.memory import MemoryLayer, QueryMode, QueryRouter
from monad.cognition.organs.base import OrganResult
from monad.cognition.reasoning import ModelRouter, ModelTier, ReflexionEngine, TaskComplexity
from monad.cognition.self_model import SelfModel


# ---------------------------------------------------------------------------
# 1. Organ registry
# ---------------------------------------------------------------------------

def test_register_all_produces_82_organs():
    """The canonical Cognitive Architecture spec defines 82 organs
    (57 human_genius + 6 animal + 15 microbial + 4 conceptual)."""
    reg = register_all()
    counts = reg.counts()
    assert counts["human_genius"] == 57
    assert counts["animal_extreme"] == 6
    assert counts["microbial"] == 15
    assert counts["conceptual"] == 4
    assert counts["total"] == 82


def test_registry_has_canonical_high_stakes_organs():
    """Executive default organ selection references these by name."""
    reg = register_all()
    for name in ("Ruin Detector", "Pattern Hunger", "Entropy Pulse",
                 "Recursive Memory", "Collective Mind"):
        assert reg.has(name), f"missing canonical organ: {name}"


def test_registry_has_canonical_animal_organs():
    reg = register_all()
    for name in ("Phoenix Protocol", "Octopus", "Adaptive Reprogramming"):
        # Names present as either name or inspiration
        found = reg.has(name) or any(o.inspiration == name for o in reg.all())
        assert found, f"missing canonical animal organ or inspiration: {name}"


def test_registry_get_and_by_category():
    reg = register_all()
    animals = reg.list_by_category(OrganCategory.ANIMAL_EXTREME)
    assert len(animals) == 6
    for a in animals:
        assert reg.get(a.name) is a


def test_registry_rejects_duplicates():
    reg = register_all()
    with pytest.raises(ValueError):
        reg.register(reg.all()[0])


# ---------------------------------------------------------------------------
# 2. Executive
# ---------------------------------------------------------------------------

def _r(name, output, conf, votes=None):
    return OrganResult(organ_name=name, output=output, confidence=conf,
                       votes=votes or {})


def test_executive_highest_confidence():
    exec_ = ExecutiveController(strategy="highest_confidence")
    d = exec_.decide([_r("a", "A", 0.4), _r("b", "B", 0.9), _r("c", "C", 0.6)])
    assert d.winning_organs == ["b"]
    assert d.final_output == "B"


def test_executive_weighted_vote():
    exec_ = ExecutiveController(strategy="weighted_vote")
    d = exec_.decide([
        _r("a", "answer1", 0.6, votes={"paris": 1.0}),
        _r("b", "answer2", 0.9, votes={"paris": 1.0}),
        _r("c", "answer3", 0.5, votes={"london": 1.0}),
    ])
    assert "paris" in d.tally
    assert d.tally["paris"] > d.tally["london"]


def test_executive_triggers_reflexion_on_low_confidence():
    engine = ReflexionEngine()  # heuristic-only, no LLM
    exec_ = ExecutiveController(
        strategy="highest_confidence",
        reflexion_threshold=0.5,
        reflexion_engine=engine,
    )
    d = exec_.decide([_r("weak", "I don't know", 0.1)], prompt="What is X?")
    assert d.reflexion_triggered is True


# ---------------------------------------------------------------------------
# 3. Self-model
# ---------------------------------------------------------------------------

def test_self_model_build_and_record():
    sm = SelfModel().build()
    beliefs = sm.by_kind("belief")
    assert any("Monad" in n.label for n in beliefs)
    cyc = sm.record_cycle("hello", {"confidence": 0.7})
    sm.record_activation("thought_experimentalist", {"confidence": 0.8}, cycle_idx=cyc)
    stats = sm.stats()
    assert stats["by_kind"]["cycle"] == 1
    assert stats["by_kind"]["activation"] == 1


def test_self_model_conflict():
    sm = SelfModel().build()
    sm.add_conflict("A vs B", ["A", "B"], "A")
    assert len(sm.by_kind("conflict")) == 1


# ---------------------------------------------------------------------------
# 4. Memory + QueryRouter
# ---------------------------------------------------------------------------

def test_memory_remember_recall_forget():
    mem = MemoryLayer(backend="inmem")
    mem.remember("Einstein discovered relativity. Newton invented calculus.")
    hits = mem.recall("relativity")
    assert any("relativity" in h["text"].lower() for h in hits)
    removed = mem.forget("Newton")
    assert removed >= 1


def test_query_router_routes():
    qr = QueryRouter()
    assert qr.route("What is the connection between Einstein and Poincaré?") == QueryMode.GRAPH_ONLY
    assert qr.route("Explain how it feels to be conscious") == QueryMode.VECTOR_ONLY
    assert qr.route("What happened yesterday?") == QueryMode.TEMPORAL
    assert qr.route("hi") == QueryMode.FEELING_LUCKY
    assert qr.route("Compare python and rust") == QueryMode.HYBRID


# ---------------------------------------------------------------------------
# 5. Model router
# ---------------------------------------------------------------------------

def test_model_router_classifies():
    r = ModelRouter()
    assert r.classify("hi") == TaskComplexity.TRIVIAL
    assert r.classify("write a python function to reverse a string") == TaskComplexity.COMPLEX
    assert r.classify("design an end-to-end distributed database from scratch") == TaskComplexity.FRONTIER


def test_model_router_routes_local_only_by_default(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    r = ModelRouter()
    dec = r.route("design a cathedral")
    assert dec.tier in (ModelTier.LOCAL_STRONG, ModelTier.LOCAL_FAST)


def test_model_router_uses_cloud_when_key_present(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    r = ModelRouter()
    dec = r.route("design a cathedral end-to-end from scratch")
    assert dec.tier == ModelTier.CLOUD_FRONTIER


# ---------------------------------------------------------------------------
# 6. Reflexion
# ---------------------------------------------------------------------------

def test_reflexion_heuristic_improves_short_draft():
    engine = ReflexionEngine()
    trace = engine.reflect_and_revise_traced(
        prompt="What is 2+2?",
        draft="I'm not sure",
    )
    assert "uncertainty" in trace.critique.lower() or "short" in trace.critique.lower()
    assert trace.revised != trace.original


# ---------------------------------------------------------------------------
# 7. Full Monad
# ---------------------------------------------------------------------------

def test_monad_think_returns_cycle_with_output():
    m = Monad(MonadConfig(max_organs_per_cycle=4))
    cycle = m.think("what is the meaning of intelligence?")
    assert cycle.prompt.startswith("what is")
    assert cycle.decision is not None
    assert len(cycle.activated_organs) <= 4
    assert cycle.output


def test_monad_info():
    m = Monad(MonadConfig())
    info = m.info()
    assert info["organs"]["total"] == 82
    assert "memory" in info
    assert "self_model" in info


def test_monad_can_export_organs_as_mcp_tools():
    m = Monad(MonadConfig(register_all_as_mcp_tools=True, max_organs_per_cycle=2))
    tools = m.mcp.list_tools()
    assert len(tools) == 82
    # Invoke one uniformly
    result = m.mcp.invoke(tools[0]["name"], {"prompt": "test"})
    assert "organ_name" in result


# ---------------------------------------------------------------------------
# 8. ModelRouter — Cognitive Architecture spec API
# ---------------------------------------------------------------------------

def test_model_router_select_sensitive_forces_local():
    r = ModelRouter()
    m = r.select("private data", TaskComplexity.SENSITIVE)
    assert m.provider == "ollama"
    assert "mistral" in m.model_id


def test_model_router_select_code_uses_deepseek():
    r = ModelRouter()
    m = r.select("sort algorithm", TaskComplexity.CODE)
    assert "deepseek" in m.model_id


def test_model_router_prefer_local_forces_mistral(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    r = ModelRouter(prefer_local=True)
    m = r.select("hard task", TaskComplexity.FRONTIER)
    assert m.provider == "ollama"


def test_model_router_high_stakes_organ_gets_frontier_when_cloud(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    r = ModelRouter()
    m = r.select_for_organ("Ruin Detector", 0.9)
    assert m.tier.value == "cloud_frontier"


def test_model_router_low_stakes_organ_stays_local():
    r = ModelRouter()
    m = r.select_for_organ("Narrative Mastery", 0.3)
    assert m.provider == "ollama"


# ---------------------------------------------------------------------------
# 9. MonadMCPServer — 3 default Monad tools
# ---------------------------------------------------------------------------

def test_monad_mcp_server_has_three_default_tools():
    from monad.cognition.mcp import MonadMCPServer
    m = Monad(MonadConfig(max_organs_per_cycle=1))
    server = MonadMCPServer(monad_instance=m)
    tool_names = {t["name"] for t in server.list_tools()}
    assert "monad_recall" in tool_names
    assert "monad_organ_analyze" in tool_names
    assert "monad_self_model_query" in tool_names


def test_monad_mcp_recall_returns_results():
    from monad.cognition.mcp import MonadMCPServer
    m = Monad(MonadConfig(max_organs_per_cycle=1))
    m.memory.remember("Einstein discovered relativity.")
    server = MonadMCPServer(monad_instance=m)
    result = server.invoke("monad_recall", {"query": "relativity"})
    assert result["tool"] == "monad_recall"
    assert isinstance(result["results"], list)


def test_monad_mcp_organ_analyze_runs_organ():
    from monad.cognition.mcp import MonadMCPServer
    m = Monad(MonadConfig(max_organs_per_cycle=1))
    server = MonadMCPServer(monad_instance=m)
    result = server.invoke("monad_organ_analyze",
                           {"organ": "Ruin Detector", "context": "test market volatility"})
    assert result["tool"] == "monad_organ_analyze"
    assert result["organ"] == "Ruin Detector"
    assert "result" in result


def test_monad_mcp_self_model_query():
    from monad.cognition.mcp import MonadMCPServer
    m = Monad(MonadConfig(max_organs_per_cycle=1))
    server = MonadMCPServer(monad_instance=m)
    result = server.invoke("monad_self_model_query", {"question": "who am I?"})
    assert result["tool"] == "monad_self_model_query"
    assert "beliefs" in result
    assert any("Monad" in b for b in result["beliefs"])
