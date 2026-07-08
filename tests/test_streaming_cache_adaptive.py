"""Tests for Builds #018 (streaming), #020 (adaptive), #024 (cache)."""

from __future__ import annotations

import time

import pytest

from monad.orchestration import (
    AdaptiveRouter, CacheEntry, ResponseCache,
    StreamChunk, StreamingResponse, fake_stream, real_stream,
)


# ---------------------------------------------------------------------------
# Streaming (Build #018)
# ---------------------------------------------------------------------------

def test_fake_stream_yields_all_text():
    stream = fake_stream("hello world", chunk_size=3, delay_s=0)
    chunks = list(stream)
    reconstructed = "".join(c.text for c in chunks)
    assert reconstructed == "hello world"
    assert chunks[-1].done is True


def test_fake_stream_final_chunk_has_metadata():
    stream = fake_stream("x", chunk_size=1, delay_s=0,
                          metadata_final={"model": "test", "latency_ms": 42})
    chunks = list(stream)
    final = chunks[-1]
    assert final.done is True
    assert final.metadata["model"] == "test"


def test_fake_stream_to_sse_format():
    stream = fake_stream("abc", chunk_size=1, delay_s=0)
    lines = list(stream.to_sse())
    assert all(l.startswith("data: ") for l in lines)
    assert all(l.endswith("\n\n") for l in lines)
    import json
    payloads = [json.loads(l.removeprefix("data: ").strip()) for l in lines]
    assert payloads[-1]["done"] is True


def test_fake_stream_accumulates_text_property():
    stream = fake_stream("Hello, Monad!", chunk_size=3, delay_s=0)
    for _ in stream:
        pass
    assert stream.text == "Hello, Monad!"
    assert stream.done is True


def test_real_stream_falls_back_to_generate_on_error():
    """If provider.stream() raises, we should still get at least an error chunk."""
    class BrokenProvider:
        def stream(self, *a, **kw):
            raise RuntimeError("no stream")
    stream = real_stream(BrokenProvider(), "m", "prompt", metadata_final={"x": 1})
    chunks = list(stream)
    assert any("stream error" in c.text for c in chunks)
    assert chunks[-1].done is True


# ---------------------------------------------------------------------------
# Response cache (Build #024)
# ---------------------------------------------------------------------------

def test_cache_put_and_get_lru(tmp_path):
    cache = ResponseCache(db_path=tmp_path / "cache.db", lru_size=4)
    key = ResponseCache.make_key("modelA", "hello", temperature=0.7)
    cache.put(CacheEntry(key=key, text="world", model_id="modelA"))
    hit = cache.get(key)
    assert hit is not None
    assert hit.text == "world"
    assert hit.hit_count == 1


def test_cache_persistent_across_instances(tmp_path):
    db = tmp_path / "cache.db"
    c1 = ResponseCache(db_path=db)
    key = ResponseCache.make_key("m", "hi")
    c1.put(CacheEntry(key=key, text="reply", model_id="m"))
    c1.close()

    c2 = ResponseCache(db_path=db)
    hit = c2.get(key)
    assert hit is not None
    assert hit.text == "reply"


def test_cache_lru_evicts():
    cache = ResponseCache(db_path=None, lru_size=2)
    for i in range(4):
        k = f"k{i}"
        cache.put(CacheEntry(key=k, text=f"v{i}", model_id="m"))
    # Only the last 2 should remain in LRU
    assert cache.get("k0") is None
    assert cache.get("k3") is not None


def test_cache_skips_stub_responses(tmp_path):
    cache = ResponseCache(db_path=tmp_path / "c.db")
    key = "k1"
    cache.put(CacheEntry(key=key, text="[stub reply] blah", model_id="m"))
    assert cache.get(key) is None    # skipped


def test_cache_key_stability():
    k1 = ResponseCache.make_key("m", "hello", temperature=0.7, max_tokens=100)
    k2 = ResponseCache.make_key("m", "hello", max_tokens=100, temperature=0.7)
    assert k1 == k2   # key is param-order-independent


def test_cache_size_stats(tmp_path):
    cache = ResponseCache(db_path=tmp_path / "c.db")
    cache.put(CacheEntry(key="a", text="A", model_id="m"))
    cache.put(CacheEntry(key="b", text="B", model_id="m"))
    stats = cache.size()
    assert stats["persisted_entries"] == 2
    assert stats["lru_entries"] == 2


def test_cache_clear(tmp_path):
    cache = ResponseCache(db_path=tmp_path / "c.db")
    cache.put(CacheEntry(key="a", text="A", model_id="m"))
    assert cache.clear() >= 1
    assert cache.get("a") is None


# ---------------------------------------------------------------------------
# Adaptive router (Build #020)
# ---------------------------------------------------------------------------

def test_adaptive_records_and_recovers(tmp_path):
    router = AdaptiveRouter(db_path=tmp_path / "r.db", exploration=0.0)
    router.record(intent="coding", strategy="verification",
                  success=True, latency_ms=1200, confidence=0.8)
    router.record(intent="coding", strategy="verification",
                  success=True, latency_ms=1000, confidence=0.9)
    stats = router.stats(intent="coding")
    v = [s for s in stats if s.strategy == "verification"][0]
    assert v.trials == 2
    assert v.successes == 2
    assert v.success_rate == 1.0


def test_adaptive_picks_winning_strategy_over_time(tmp_path):
    router = AdaptiveRouter(db_path=tmp_path / "r.db", exploration=0.0)
    # Feed clear signal: cascade always wins for questions
    for _ in range(30):
        router.record("question", "cascade", success=True,
                      latency_ms=500, confidence=0.9)
    for _ in range(30):
        router.record("question", "ensemble", success=False,
                      latency_ms=3000, confidence=0.1)

    # Take multiple samples; cascade should dominate
    picks = [router.select("question", allowed=["cascade", "ensemble"])
             for _ in range(50)]
    cascade_ratio = picks.count("cascade") / len(picks)
    assert cascade_ratio > 0.75


def test_adaptive_exploration_diversifies_choices(tmp_path):
    router = AdaptiveRouter(db_path=tmp_path / "r.db", exploration=1.0)
    # 100% exploration → should hit multiple strategies
    picks = {router.select("chat", allowed=["a", "b", "c"]) for _ in range(30)}
    assert len(picks) >= 2


def test_adaptive_persistent(tmp_path):
    db = tmp_path / "r.db"
    r1 = AdaptiveRouter(db_path=db)
    r1.record("chat", "domain_routing", True, 100, 0.9)
    r1.close()
    r2 = AdaptiveRouter(db_path=db)
    stats = r2.stats(intent="chat")
    assert any(s.strategy == "domain_routing" and s.trials == 1 for s in stats)
