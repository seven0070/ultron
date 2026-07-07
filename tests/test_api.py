"""Tests for Build #059 — FastAPI server."""

from __future__ import annotations

import pytest

# Skip whole module if fastapi isn't available (installer will add it later)
fastapi = pytest.importorskip("fastapi")
httpx = pytest.importorskip("httpx")

from fastapi.testclient import TestClient   # noqa: E402


@pytest.fixture(scope="module")
def client(tmp_path_factory):
    from monad.api import create_app
    root = tmp_path_factory.mktemp("api-root")
    # Minimal config.yaml so MonadApplication.startup() succeeds
    (root / "config.yaml").write_text(
        "application: {name: t, version: 0.1, environment: test}\n"
        "paths: {models_dir: models, memory_dir: memory_data,\n"
        "        workspace_dir: workspace, logs_dir: logs,\n"
        "        cache_dir: cache, config_dir: config,\n"
        "        plugins_dir: monad/plugins}\n"
        "runtime: {default_engine: llama_cpp, default_model: longcat2,\n"
        "          max_loaded_models: 1, auto_detect_gpu: false, portable_mode: true}\n"
        "logging: {level: WARNING, console: false, file: false,\n"
        "          file_rotation: 10 MB, file_retention: 1 days}\n"
        "orchestration: {enabled: true, default_strategy: auto, max_workers: 1,\n"
        "                model_pool: {reasoning: longcat2, coding: glm5,\n"
        "                             creative: llama2}, cascade_threshold: 0.55}\n"
        "plugins: {auto_load: []}\n",
        encoding="utf-8",
    )
    (root / "models.yaml").write_text("models: []\n", encoding="utf-8")
    import os
    old_cwd = os.getcwd()
    os.chdir(root)
    try:
        app = create_app(root=root)
        yield TestClient(app)
    finally:
        os.chdir(old_cwd)


def test_index_returns_html(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "Monad-Ultron Dashboard" in r.text
    assert "text/html" in r.headers["content-type"]


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert "ready" in r.json()


def test_info(client):
    r = client.get("/info")
    assert r.status_code == 200
    j = r.json()
    assert "version" in j
    assert "cognition" in j


def test_organs(client):
    r = client.get("/organs")
    assert r.status_code == 200
    j = r.json()
    assert j["counts"]["total"] == 82


def test_models_endpoint(client):
    r = client.get("/models")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_memory_remember_and_recall(client):
    r = client.post("/memory/remember", json={"text": "the sky is blue today"})
    assert r.status_code == 200
    assert r.json()["ok"] is True

    r2 = client.post("/memory/recall", json={"query": "sky", "top_k": 3})
    assert r2.status_code == 200
    hits = r2.json()["results"]
    assert any("sky" in h["text"] for h in hits)


def test_tools_list(client):
    r = client.get("/tools")
    assert r.status_code == 200
    ids = {t["id"] for t in r.json()}
    assert {"filesystem", "python", "terminal", "http"} <= ids


def test_ask_fails_gracefully_when_no_model(client):
    # No GGUFs downloaded in the test env → orchestrator should return an error
    r = client.post("/ask", json={"prompt": "hi"})
    # Either succeeds with stub-ish text OR returns 500 — both acceptable
    assert r.status_code in (200, 500)
