"""Tests for Build #036–#040 — Tool framework."""

from __future__ import annotations

import pytest

from monad.tools import (
    FilesystemTool, HTTPTool, PythonSandboxTool, TerminalTool,
    ToolRegistry, default_registry,
)


# ---------------------------------------------------------------------------
# FilesystemTool
# ---------------------------------------------------------------------------

def test_fs_write_read_roundtrip(tmp_path):
    fs = FilesystemTool(workspace_dir=tmp_path)
    r = fs.invoke(op="write", path="notes/hello.txt", content="hi there")
    assert r.ok
    r2 = fs.invoke(op="read", path="notes/hello.txt")
    assert r2.ok
    assert r2.output == "hi there"


def test_fs_list(tmp_path):
    fs = FilesystemTool(workspace_dir=tmp_path)
    fs.invoke(op="write", path="a.txt", content="A")
    fs.invoke(op="write", path="b.txt", content="B")
    r = fs.invoke(op="list", path="")
    assert r.ok
    names = [e["name"] for e in r.output["entries"]]
    assert "a.txt" in names and "b.txt" in names


def test_fs_delete(tmp_path):
    fs = FilesystemTool(workspace_dir=tmp_path)
    fs.invoke(op="write", path="doomed.txt", content="x")
    r = fs.invoke(op="delete", path="doomed.txt")
    assert r.ok
    r2 = fs.invoke(op="read", path="doomed.txt")
    assert not r2.ok


def test_fs_sandbox_rejects_escape(tmp_path):
    fs = FilesystemTool(workspace_dir=tmp_path)
    r = fs.invoke(op="read", path="../../../etc/passwd")
    assert not r.ok
    assert "escape" in r.error.lower()


def test_fs_unknown_op(tmp_path):
    fs = FilesystemTool(workspace_dir=tmp_path)
    r = fs.invoke(op="haxx", path="x")
    assert not r.ok


# ---------------------------------------------------------------------------
# PythonSandboxTool
# ---------------------------------------------------------------------------

def test_python_sandbox_runs_code():
    py = PythonSandboxTool()
    r = py.invoke(code="print(2 + 2)")
    assert r.ok
    assert "4" in r.output["stdout"]


def test_python_sandbox_captures_error():
    py = PythonSandboxTool()
    r = py.invoke(code="raise ValueError('boom')")
    assert not r.ok
    assert "ValueError" in r.output["stderr"] or "ValueError" in r.error


def test_python_sandbox_timeout():
    py = PythonSandboxTool()
    r = py.invoke(code="import time; time.sleep(5)", timeout_s=0.5)
    assert not r.ok
    assert "timeout" in r.error.lower()


def test_python_sandbox_empty():
    py = PythonSandboxTool()
    r = py.invoke(code="   ")
    assert not r.ok


# ---------------------------------------------------------------------------
# TerminalTool
# ---------------------------------------------------------------------------

def test_terminal_allowed_command():
    t = TerminalTool()
    r = t.invoke(command="echo hello")
    assert r.ok
    assert "hello" in r.output["stdout"]


def test_terminal_disallowed_command():
    t = TerminalTool()
    r = t.invoke(command="rm -rf /")
    assert not r.ok
    assert "allowlist" in r.error


def test_terminal_empty():
    t = TerminalTool()
    r = t.invoke(command="")
    assert not r.ok


# ---------------------------------------------------------------------------
# HTTPTool
# ---------------------------------------------------------------------------

def test_http_rejects_non_http_scheme():
    h = HTTPTool()
    r = h.invoke(url="ftp://example.com/x")
    assert not r.ok
    assert "http" in r.error.lower()


def test_http_rejects_localhost():
    h = HTTPTool()
    r = h.invoke(url="http://localhost:8080/x")
    assert not r.ok
    assert "blocked" in r.error.lower() or "ssrf" in r.error.lower()


def test_http_rejects_private_ip():
    h = HTTPTool()
    r = h.invoke(url="http://192.168.1.1/x")
    assert not r.ok


# ---------------------------------------------------------------------------
# ToolRegistry + PolicyGate integration
# ---------------------------------------------------------------------------

def test_registry_invokes_through_policy_gate(tmp_path):
    from monad.policy import ApprovalMode, PolicyGate
    gate = PolicyGate(
        require_approval_for=["tool.filesystem.fs"],
        default_mode=ApprovalMode.AUTO_NO,
    )
    reg = ToolRegistry(policy_gate=gate)
    reg.register(FilesystemTool(workspace_dir=tmp_path))
    r = reg.invoke("filesystem", op="write", path="x.txt", content="denied?")
    assert not r.ok
    assert "policy" in r.error.lower() or "denied" in r.error.lower()


def test_default_registry_has_all_tools(tmp_path):
    reg = default_registry(workspace_dir=tmp_path)
    ids = {t.id for t in reg.list()}
    assert ids == {"filesystem", "python", "terminal", "http"}
