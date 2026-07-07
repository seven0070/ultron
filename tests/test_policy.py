"""Tests for Build #056 — Real PolicyGate."""

from __future__ import annotations

from monad.policy import ApprovalMode, PolicyGate


def test_gate_ignores_actions_not_in_require_list():
    g = PolicyGate(require_approval_for=["dangerous.thing"])
    assert g.check("harmless.thing") is True


def test_gate_auto_yes_and_auto_no():
    g = PolicyGate(require_approval_for=["x"], default_mode=ApprovalMode.AUTO_YES)
    assert g.check("x") is True
    g2 = PolicyGate(require_approval_for=["x"], default_mode=ApprovalMode.AUTO_NO)
    assert g2.check("x") is False


def test_gate_per_action_override():
    g = PolicyGate(require_approval_for=["x", "y"], default_mode=ApprovalMode.AUTO_YES)
    g.set_mode("y", ApprovalMode.DENY)
    assert g.check("x") is True
    assert g.check("y") is False


def test_gate_prefix_matching():
    g = PolicyGate(require_approval_for=["tool."], default_mode=ApprovalMode.AUTO_NO)
    assert g.check("tool.filesystem.write") is False
    assert g.check("plugin.enable") is True   # doesn't match "tool."


def test_gate_custom_prompt_fn(monkeypatch):
    monkeypatch.delenv("MONAD_POLICY_DEFAULT", raising=False)
    calls = []
    def custom_prompt(req):
        calls.append(req.action)
        # Approve only "do.safe", deny everything else (including do.dangerous)
        return req.action == "do.safe"
    g = PolicyGate(
        require_approval_for=["do.safe", "do.dangerous"],
        default_mode=ApprovalMode.PROMPT,
        prompt_fn=custom_prompt,
    )
    assert g.check("do.safe") is True
    assert g.check("do.dangerous") is False
    assert calls == ["do.safe", "do.dangerous"]


def test_gate_audit_records(tmp_path):
    g = PolicyGate(
        require_approval_for=["a"],
        default_mode=ApprovalMode.AUTO_YES,
        audit_db=tmp_path / "audit.db",
    )
    g.check("a", reason="unit test")
    g.check("a", reason="second")
    hist = g.audit_history(limit=10)
    assert len(hist) >= 2
    assert all(h["action"] == "a" for h in hist)


def test_gate_env_override(monkeypatch):
    monkeypatch.setenv("MONAD_POLICY_DEFAULT", "yes")
    g = PolicyGate(require_approval_for=["z"], default_mode=ApprovalMode.PROMPT)
    assert g.check("z") is True

    monkeypatch.setenv("MONAD_POLICY_DEFAULT", "no")
    assert g.check("z") is False
