"""Tests for Build #026 — Real memory layer."""

from __future__ import annotations

import pytest

from monad.memory import Memory, MemoryStore, VectorStore, RetrievalEngine


# ---------------------------------------------------------------------------
# MemoryStore (SQLite)
# ---------------------------------------------------------------------------

def test_store_put_get_delete(tmp_path):
    s = MemoryStore(tmp_path / "m.db")
    s.put("foo", "bar")
    assert s.get("foo") == "bar"
    s.put("num", 42)
    assert s.get("num") == 42
    s.put("obj", {"k": "v"})
    assert s.get("obj") == {"k": "v"}
    assert s.delete("foo") is True
    assert s.get("foo") is None


def test_store_keys_prefix(tmp_path):
    s = MemoryStore(tmp_path / "m.db")
    for k in ("a:1", "a:2", "b:1"):
        s.put(k, "x")
    assert s.keys("a:") == ["a:1", "a:2"]


def test_store_events_append_and_recent(tmp_path):
    s = MemoryStore(tmp_path / "m.db")
    id1 = s.append_event("user_msg", "hello world", tag="cli")
    id2 = s.append_event("assistant_msg", "hi there")
    assert id2 > id1
    events = s.recent_events(limit=5)
    assert len(events) == 2
    assert events[0].id == id2
    filtered = s.recent_events(kind="user_msg")
    assert len(filtered) == 1
    assert filtered[0].content == "hello world"


def test_store_search_events(tmp_path):
    s = MemoryStore(tmp_path / "m.db")
    s.append_event("note", "Einstein discovered relativity")
    s.append_event("note", "Newton invented calculus")
    hits = s.search_events("relativity")
    assert len(hits) == 1
    assert "Einstein" in hits[0].content


def test_store_size_and_clear(tmp_path):
    s = MemoryStore(tmp_path / "m.db")
    s.put("x", "y")
    s.append_event("k", "c")
    size = s.size()
    assert size["kv_keys"] == 1
    assert size["events"] == 1
    s.clear()
    assert s.size()["events"] == 0


# ---------------------------------------------------------------------------
# VectorStore
# ---------------------------------------------------------------------------

def test_vector_add_query_delete(tmp_path):
    v = VectorStore(persist_dir=tmp_path / "v")
    v.add("d1", "the quick brown fox jumps over the lazy dog")
    v.add("d2", "python programming with type hints")
    v.add("d3", "machine learning with neural networks")

    hits = v.query("quick fox", top_k=3)
    ids = [h[0] for h in hits]
    assert "d1" in ids
    assert hits[0][0] == "d1"        # substring bonus should put it first

    # Deletion
    assert v.delete("d1") is True
    hits2 = v.query("quick fox", top_k=3)
    assert "d1" not in [h[0] for h in hits2]


def test_vector_size(tmp_path):
    v = VectorStore(persist_dir=tmp_path / "v")
    v.add("a", "one")
    v.add("b", "two")
    size = v.size()
    assert size["count"] == 2


def test_vector_persistence_roundtrip(tmp_path):
    v1 = VectorStore(persist_dir=tmp_path / "v")
    v1.add("persisted", "this survives restart")
    v2 = VectorStore(persist_dir=tmp_path / "v")
    hits = v2.query("survives", top_k=1)
    assert hits and hits[0][0] == "persisted"


# ---------------------------------------------------------------------------
# RetrievalEngine (RRF hybrid)
# ---------------------------------------------------------------------------

def test_retrieval_hybrid_finds_relevant(tmp_path):
    m = Memory(tmp_path)
    m.remember("Einstein published the theory of relativity in 1915")
    m.remember("Newton wrote the Principia in 1687")
    m.remember("Feynman won the Nobel Prize for quantum electrodynamics")

    hits = m.recall("relativity", top_k=3)
    assert hits
    assert any("Einstein" in h.text for h in hits)


def test_retrieval_modes(tmp_path):
    m = Memory(tmp_path)
    m.remember("apple banana cherry")
    m.remember("dog eagle falcon")

    kw = m.retrieval.retrieve("apple", mode="keyword")
    vec = m.retrieval.retrieve("apple", mode="vector")
    hy = m.retrieval.retrieve("apple", mode="hybrid")
    assert kw and vec and hy
    assert kw[0].source == "keyword"
    assert vec[0].source == "vector"
    assert hy[0].source == "hybrid"


# ---------------------------------------------------------------------------
# Memory facade
# ---------------------------------------------------------------------------

def test_memory_facade_remember_recall_forget(tmp_path):
    m = Memory(tmp_path)
    m.remember("Monad is a portable AI OS")
    m.remember("Monad uses Cognee for memory")
    hits = m.recall("Monad", top_k=5)
    assert len(hits) >= 1
    forgot = m.forget("Cognee")
    assert forgot >= 1
    hits2 = m.recall("Cognee", top_k=5)
    assert not any("Cognee" in h.text for h in hits2)


def test_memory_size(tmp_path):
    m = Memory(tmp_path)
    m.remember("x")
    s = m.size()
    assert s["store"]["events"] == 1
    assert s["vectors"]["count"] == 1
