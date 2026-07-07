"""Tests for Build #017a — Self-Improvement Framework."""

from pathlib import Path

import pytest

from monad.evolution.evolvable import (
    DEFAULT_POLICIES, EvolutionZone, is_path_allowed,
)
from monad.evolution.log import ChangeType, EvolutionLog, EvolutionRecord, Outcome
from monad.evolution.manager import EvolutionManager
from monad.evolution.proposer import PatchProposer
from monad.evolution.rollback import RollbackManager
from monad.evolution.sandbox import SandboxRunner


# ---------------------------------------------------------------------------
# Safety boundaries
# ---------------------------------------------------------------------------

def test_forbidden_paths_rejected():
    for bad in [
        "monad/core/application.py",
        "monad/evolution/manager.py",
        "monad/policy/stubs.py",
        "monad/inference/llama_cpp_provider.py",
        ".git/HEAD",
        "python_portable/python.exe",
        "models/llama2/llama2.gguf",
    ]:
        ok, reason = is_path_allowed(bad)
        assert not ok, f"{bad} should be forbidden but was allowed: {reason}"


def test_allowed_paths_accepted():
    for good in [
        "monad/plugins/my_new_plugin.py",
        "monad/tools/impl/my_tool.py",
        "monad/prompts/custom/coding_v2.txt",
        "config.yaml",
        "models.yaml",
    ]:
        ok, reason = is_path_allowed(good)
        assert ok, f"{good} should be allowed but was rejected: {reason}"


def test_default_policies_complete():
    for zone in EvolutionZone:
        assert zone in DEFAULT_POLICIES
        policy = DEFAULT_POLICIES[zone]
        assert policy.max_lines > 0
        assert isinstance(policy.path_globs, list)


# ---------------------------------------------------------------------------
# EvolutionLog
# ---------------------------------------------------------------------------

def test_log_record_and_get(tmp_path):
    db = tmp_path / "evo.db"
    elog = EvolutionLog(db)
    rec = EvolutionRecord(
        id=EvolutionLog.new_id(),
        timestamp="2026-07-07T12:00:00",
        change_type=ChangeType.NEW_PLUGIN,
        outcome=Outcome.PROPOSED,
        goal="add a Hello plugin",
        target_path="monad/plugins/hello.py",
        diff="+ hello",
    )
    elog.record(rec)
    got = elog.get(rec.id)
    assert got is not None
    assert got.goal == "add a Hello plugin"
    assert got.change_type == ChangeType.NEW_PLUGIN


def test_log_update_outcome(tmp_path):
    elog = EvolutionLog(tmp_path / "evo.db")
    rec = EvolutionRecord(
        id="evo-test", timestamp="t", change_type=ChangeType.PATCH_PROMPT,
        outcome=Outcome.PROPOSED, goal="g", target_path="p", diff="",
    )
    elog.record(rec)
    elog.update_outcome("evo-test", Outcome.APPLIED, tests_passed=True,
                        test_output="ok")
    got = elog.get("evo-test")
    assert got.outcome == Outcome.APPLIED
    assert got.tests_passed is True


def test_history(tmp_path):
    elog = EvolutionLog(tmp_path / "evo.db")
    for i in range(3):
        elog.record(EvolutionRecord(
            id=f"evo-{i}", timestamp=f"2026-07-07T00:0{i}",
            change_type=ChangeType.PATCH_PROMPT,
            outcome=Outcome.PROPOSED, goal=f"g{i}", target_path="p", diff="",
        ))
    hist = elog.history(limit=10)
    assert len(hist) == 3


# ---------------------------------------------------------------------------
# Proposer (stub mode — no LLM available)
# ---------------------------------------------------------------------------

def test_proposer_stub_fallback(tmp_path):
    (tmp_path / "monad" / "plugins").mkdir(parents=True)
    target = tmp_path / "monad" / "plugins" / "greeter.py"
    target.write_text("# original\n", encoding="utf-8")

    p = PatchProposer(root=tmp_path, inference_manager=None, model_manager=None)
    proposal = p.propose(
        goal="make it greet the user",
        zone=EvolutionZone.PLUGINS,
        target_path="monad/plugins/greeter.py",
    )
    assert proposal.model_used == "stub"
    assert "TODO(monad-evolution)" in proposal.proposed_content
    assert "# original" in proposal.proposed_content
    assert "no_llm_available" in proposal.warnings


def test_proposer_rejects_forbidden(tmp_path):
    p = PatchProposer(root=tmp_path)
    with pytest.raises(PermissionError):
        p.propose(
            goal="anything",
            zone=EvolutionZone.PLUGINS,
            target_path="monad/core/application.py",
        )


# ---------------------------------------------------------------------------
# Rollback
# ---------------------------------------------------------------------------

def test_backup_and_restore(tmp_path):
    (tmp_path / "monad" / "plugins").mkdir(parents=True)
    target = tmp_path / "monad" / "plugins" / "x.py"
    target.write_text("v1", encoding="utf-8")

    rb = RollbackManager(root=tmp_path, backups_dir=tmp_path / "backups")
    backup = rb.backup("monad/plugins/x.py", "rec-1")
    assert Path(backup).exists()

    target.write_text("v2", encoding="utf-8")

    class R:
        id = "rec-1"
        target_path = "monad/plugins/x.py"

    assert rb.rollback(R())
    assert target.read_text(encoding="utf-8") == "v1"


def test_rollback_of_new_file(tmp_path):
    (tmp_path / "monad" / "plugins").mkdir(parents=True)
    rb = RollbackManager(root=tmp_path, backups_dir=tmp_path / "backups")
    # file did not exist before
    rb.backup("monad/plugins/new.py", "rec-2")
    # simulate creation
    new_file = tmp_path / "monad" / "plugins" / "new.py"
    new_file.write_text("created", encoding="utf-8")

    class R:
        id = "rec-2"
        target_path = "monad/plugins/new.py"

    assert rb.rollback(R())
    assert not new_file.exists()


# ---------------------------------------------------------------------------
# Full manager loop (stub-mode, no sandbox tests)
# ---------------------------------------------------------------------------

def test_manager_propose_and_apply_stub(tmp_path):
    # Minimal repo layout
    (tmp_path / "monad" / "plugins").mkdir(parents=True)

    elog = EvolutionLog(tmp_path / "memory_data" / "evolution.db")
    proposer = PatchProposer(root=tmp_path)
    sandbox = SandboxRunner(root=tmp_path)
    rollback = RollbackManager(root=tmp_path,
                                backups_dir=tmp_path / "memory_data" / "backups")
    mgr = EvolutionManager(
        root=tmp_path,
        evolution_log=elog,
        proposer=proposer,
        sandbox=sandbox,
        rollback=rollback,
        policy_gate=None,
    )
    rec, proposal = mgr.propose(
        goal="create a hello plugin",
        zone=EvolutionZone.PLUGINS,
        target_path="monad/plugins/hello.py",
    )
    assert rec.outcome == Outcome.PROPOSED

    applied = mgr.apply(rec, proposal, skip_tests=True, skip_approval=True)
    assert applied.outcome == Outcome.APPLIED
    assert (tmp_path / "monad" / "plugins" / "hello.py").exists()

    # Rollback
    assert mgr.rollback_change(rec.id)
    assert not (tmp_path / "monad" / "plugins" / "hello.py").exists()
