"""
Monad FastAPI server — Build #059.

Endpoints:
  GET  /                 - HTML dashboard (self-contained, no external assets)
  GET  /health           - liveness probe
  GET  /info             - system info
  GET  /models           - list registered models
  GET  /organs           - list 82 cognitive organs
  POST /ask              - orchestrated LLM ask
  POST /memory/remember  - persist a note
  POST /memory/recall    - retrieve by query
  GET  /tools            - list tools
  POST /tools/{id}       - invoke a tool (via PolicyGate)
  GET  /policy/audit     - recent policy decisions

FastAPI is an OPTIONAL dependency. If not installed, create_app() raises with
install instructions. Everything else in Monad works without it.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from monad.core.logger import get_logger

log = get_logger(__name__)


# ---------------------------------------------------------------------------
# Request schemas — defined at module scope so pydantic can resolve forward refs
# ---------------------------------------------------------------------------

try:
    from pydantic import BaseModel

    class AskReq(BaseModel):
        prompt: str
        strategy: str = ""
        cognition: bool = False

    class FuseReq(BaseModel):
        prompt: str
        mode: str = "auto"
        max_tokens: int = 1024

    class LearnReq(BaseModel):
        source: str
        kind: str = "text"      # "text" | "url" | "repo"

    class EvolveProposeReq(BaseModel):
        goal: str
        target: str
        zone: str = "plugins"

    class RememberReq(BaseModel):
        text: str
        kind: str = "note"
        tag: str = ""

    class RecallReq(BaseModel):
        query: str
        top_k: int = 5

    class ToolInvokeReq(BaseModel):
        kwargs: dict[str, Any] = {}

except ImportError:
    AskReq = FuseReq = LearnReq = EvolveProposeReq = None  # type: ignore
    RememberReq = RecallReq = ToolInvokeReq = None  # type: ignore


def create_app(root: Path | None = None):
    """Build the FastAPI app. Raises if fastapi isn't installed."""
    try:
        from fastapi import Body, FastAPI, HTTPException
        from fastapi.responses import HTMLResponse
    except ImportError as e:
        raise RuntimeError(
            "fastapi + pydantic not installed.\n"
            "  Install: pip install 'fastapi>=0.111' uvicorn[standard]"
        ) from e

    from monad import __codename__, __version__
    from monad.core.application import MonadApplication
    from monad.memory import Memory
    from monad.tools import default_registry

    r = Path(root or ".").resolve()
    apporch = MonadApplication(root=r)
    apporch.startup(banner=False)

    memory = Memory(memory_dir=apporch.resources.memory_dir)
    tools = default_registry(workspace_dir=apporch.resources.workspace_dir)

    app = FastAPI(
        title="Monad-Ultron API",
        version=__version__,
        description=f"Portable local AI orchestration platform ({__codename__})",
    )

    # CORS for the Next.js dev server (127.0.0.1:3000)
    try:
        from fastapi.middleware.cors import CORSMiddleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=False,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    except Exception:
        pass

    # -- routes -------------------------------------------------------------

    @app.get("/", response_class=HTMLResponse)
    def index():
        return _DASHBOARD_HTML.replace("{{VERSION}}", __version__)

    @app.get("/health")
    def health():
        return apporch.health_check()

    @app.get("/info")
    def info():
        try:
            from monad.cognition import Monad, MonadConfig
            m = Monad(MonadConfig())
            cog_info = m.info()
        except Exception as e:
            cog_info = {"error": str(e)}
        return {
            "version": __version__,
            "codename": __codename__,
            "health": apporch.health_check(),
            "cognition": cog_info,
            "memory": memory.size(),
        }

    @app.get("/models")
    def models():
        from monad.models import ModelManager
        mm = ModelManager()
        if len(mm.list_models()) == 0:
            mm.load_registry(r / "models.yaml", r / "models")
        return [
            {"id": m.id, "role": m.role, "format": m.format,
             "size_gb": m.size_gb, "status": m.status.value,
             "description": m.description}
            for m in mm.list_models()
        ]

    @app.get("/organs")
    def organs():
        from monad.cognition.organs import register_all
        reg = register_all()
        return {
            "counts": reg.counts(),
            "organs": [o.info() for o in reg.all()],
        }

    @app.post("/ask")
    def ask(req: AskReq = Body(...)):
        from monad.inference import InferenceManager, LlamaCppProvider
        from monad.models import ModelManager
        from monad.orchestration import MultiModelOrchestrator

        mm = ModelManager()
        if len(mm.list_models()) == 0:
            mm.load_registry(r / "models.yaml", r / "models")
        im = InferenceManager()
        if "llama_cpp" not in im.list():
            im.register(LlamaCppProvider(), default=True)

        cfg = apporch.config
        pool = cfg.get("orchestration.model_pool", {}) if cfg else {}
        default_strategy = (cfg.get("orchestration.default_strategy", "auto")
                            if cfg else "auto")
        orch = MultiModelOrchestrator(
            inference_manager=im, model_manager=mm,
            model_pool=pool, default_strategy=default_strategy,
        )
        if req.cognition:
            try:
                from monad.cognition import Monad, MonadConfig
                orch.attach_cognition(Monad(MonadConfig(max_organs_per_cycle=4)))
            except Exception as e:
                log.warning("cognition attach failed: {}", e)

        try:
            response, trace = orch.handle_text(req.prompt, strategy_override=req.strategy)
        except Exception as e:
            raise HTTPException(500, f"orchestration failed: {e}")

        return {
            "text": response.text,
            "intent": response.intent.value if hasattr(response.intent, "value") else str(response.intent),
            "model": response.model_id,
            "latency_ms": response.latency_ms,
            "trace": {
                "strategy": trace.strategy,
                "models_invoked": trace.models_invoked,
                "escalated": trace.escalated,
                "final_model": trace.final_model,
            },
        }

    @app.post("/memory/remember")
    def remember(req: RememberReq = Body(...)):
        eid = memory.remember(req.text, kind=req.kind, tag=req.tag)
        return {"ok": True, "event_id": eid}

    @app.post("/memory/recall")
    def recall(req: RecallReq = Body(...)):
        hits = memory.recall(req.query, top_k=req.top_k)
        return {"results": [
            {"doc_id": h.doc_id, "text": h.text, "score": h.score,
             "source": h.source, "metadata": h.metadata}
            for h in hits
        ]}

    @app.get("/tools")
    def list_tools():
        return [t.info() for t in tools.list()]

    @app.post("/tools/{tool_id}")
    def invoke_tool(tool_id: str, req: ToolInvokeReq = Body(...)):
        try:
            result = tools.invoke(tool_id, **req.kwargs)
        except KeyError:
            raise HTTPException(404, f"unknown tool: {tool_id}")
        return {"tool": result.tool, "ok": result.ok,
                "output": result.output, "error": result.error,
                "metadata": result.metadata}

    @app.get("/policy/audit")
    def policy_audit(limit: int = 50):
        # If a shared PolicyGate is wired into tools, expose its audit
        gate = getattr(tools, "policy_gate", None)
        if gate is None:
            return {"audit": [], "note": "no PolicyGate wired"}
        return {"audit": gate.audit_history(limit=limit)}

    # -----------------------------------------------------------------------
    # /ask/stream — streaming version of /ask (Build #018)
    # -----------------------------------------------------------------------
    @app.post("/ask/stream")
    def ask_stream(req: AskReq = Body(...)):
        from fastapi.responses import StreamingResponse as FastAPIStreamingResponse
        from monad.inference import InferenceManager, LlamaCppProvider
        from monad.models import ModelManager
        from monad.orchestration import MultiModelOrchestrator, fake_stream

        mm = ModelManager()
        if len(mm.list_models()) == 0:
            mm.load_registry(r / "models.yaml", r / "models")
        im = InferenceManager()
        if "llama_cpp" not in im.list():
            im.register(LlamaCppProvider(), default=True)

        cfg = apporch.config
        pool = cfg.get("orchestration.model_pool", {}) if cfg else {}
        orch = MultiModelOrchestrator(
            inference_manager=im, model_manager=mm,
            model_pool=pool,
            default_strategy=(cfg.get("orchestration.default_strategy", "auto")
                              if cfg else "auto"),
        )
        try:
            response, trace = orch.handle_text(req.prompt,
                                                strategy_override=req.strategy)
        except Exception as e:
            def _err():
                import json as _j
                yield f"data: {_j.dumps({'text': f'error: {e}', 'done': True})}\n\n"
            return FastAPIStreamingResponse(_err(), media_type="text/event-stream")

        # Wrap the completed text in a typewriter stream
        meta = {"model": response.model_id, "latency_ms": response.latency_ms,
                "strategy": trace.strategy}
        stream = fake_stream(response.text, chunk_size=8, delay_s=0.02,
                              metadata_final=meta)
        return FastAPIStreamingResponse(stream.to_sse(),
                                          media_type="text/event-stream")

    # -----------------------------------------------------------------------
    # /cache/* — response cache mgmt (Build #024)
    # -----------------------------------------------------------------------
    @app.get("/cache/stats")
    def cache_stats():
        from monad.orchestration import ResponseCache
        cache_path = apporch.resources.cache_dir / "response_cache.db"
        cache = ResponseCache(db_path=cache_path)
        stats = cache.size()
        cache.close()
        return stats

    @app.post("/cache/clear")
    def cache_clear():
        from monad.orchestration import ResponseCache
        cache_path = apporch.resources.cache_dir / "response_cache.db"
        cache = ResponseCache(db_path=cache_path)
        n = cache.clear()
        cache.close()
        return {"cleared": n}

    # -----------------------------------------------------------------------
    # /adaptive/stats — adaptive router insight (Build #020)
    # -----------------------------------------------------------------------
    @app.get("/adaptive/stats")
    def adaptive_stats(intent: str = ""):
        from monad.orchestration import AdaptiveRouter
        router = AdaptiveRouter(
            db_path=apporch.resources.memory_dir / "adaptive_router.db",
        )
        stats = router.stats(intent=intent or None)
        router.close()
        return {"stats": [
            {"intent": s.intent, "strategy": s.strategy,
             "trials": s.trials, "successes": s.successes,
             "success_rate": round(s.success_rate, 3),
             "avg_latency_ms": round(s.avg_latency_ms, 1),
             "avg_confidence": round(s.avg_confidence, 3)}
            for s in stats
        ]}

    # -----------------------------------------------------------------------
    # /fuse — multi-model fusion (Build #080)
    # -----------------------------------------------------------------------
    @app.post("/fuse")
    def fuse(req: FuseReq = Body(...)):
        from monad.inference import InferenceManager, LlamaCppProvider
        from monad.models import ModelManager
        from monad.orchestration import FusionMode, FusionOrchestrator

        mm = ModelManager()
        if len(mm.list_models()) == 0:
            mm.load_registry(r / "models.yaml", r / "models")
        im = InferenceManager()
        if "llama_cpp" not in im.list():
            im.register(LlamaCppProvider(), default=True)

        cfg = apporch.config
        pool = cfg.get("orchestration.model_pool", {}) if cfg else {}

        fuser = FusionOrchestrator(im, mm, pool)
        try:
            mode = FusionMode(req.mode)
        except ValueError:
            raise HTTPException(400, f"unknown mode: {req.mode}")
        result = fuser.fuse(req.prompt, mode=mode, max_tokens=req.max_tokens)
        return {
            "text": result.text,
            "mode_used": result.mode_used,
            "models_used": result.models_used,
            "latency_ms": result.latency_ms,
            "fallback_reason": result.fallback_reason,
            "trace": result.trace,
        }

    # -----------------------------------------------------------------------
    # /learn — ingest text / url / repo into memory
    # -----------------------------------------------------------------------
    @app.post("/learn")
    def learn(req: LearnReq = Body(...)):
        source = req.source.strip()
        if not source:
            raise HTTPException(400, "empty source")

        chunks = 0
        summary = ""
        next_steps = ""

        if req.kind == "text":
            # Chunk into ~800-char slices to keep events digestible
            text = source
            slices = [text[i:i + 800] for i in range(0, len(text), 800)]
            for i, s in enumerate(slices):
                memory.remember(s, kind="learned_text",
                                tag=f"chunk-{i + 1}/{len(slices)}")
                chunks += 1
            summary = f"Ingested {len(text)} characters as {chunks} chunk(s)."

        elif req.kind == "url":
            # Fetch through the HTTPTool (SSRF-protected)
            result = tools.invoke("http", url=source)
            if not result.ok:
                raise HTTPException(400, f"fetch failed: {result.error}")
            text = result.output.get("text", "")[:20_000]
            slices = [text[i:i + 800] for i in range(0, len(text), 800)]
            for i, s in enumerate(slices):
                memory.remember(s, kind="learned_url",
                                tag=source[:80],
                                metadata={"url": source, "chunk": i})
                chunks += 1
            summary = f"Fetched {result.output.get('bytes', 0)} bytes from {source}; ingested {chunks} chunk(s)."

        elif req.kind == "repo":
            # For repos we DON'T clone (that needs git + policy). We fetch the
            # README via GitHub's raw endpoint as a lightweight analysis.
            raw_url = _guess_readme_url(source)
            summary = f"Repo detected: {source}\n\nStored the reference in memory."
            memory.remember(f"Repo of interest: {source}",
                            kind="repo_reference", tag="integrate")
            chunks = 1
            if raw_url:
                res = tools.invoke("http", url=raw_url)
                if res.ok:
                    readme = res.output.get("text", "")[:8000]
                    memory.remember(readme, kind="learned_readme",
                                    tag=source, metadata={"source": source})
                    chunks += 1
                    summary += f"\n\nFetched README ({len(readme)} chars). "
            next_steps = (
                "- `evolve: add a Monad plugin that wraps <feature> from this repo`\n"
                "- `recall <keyword>` to search what I learned\n"
                f"- Clone locally, then `learn` specific files"
            )
        else:
            raise HTTPException(400, f"unknown kind: {req.kind}")

        return {"ok": True, "chunks": chunks, "kind": req.kind,
                "summary": summary, "next_steps": next_steps}

    # -----------------------------------------------------------------------
    # /evolve/propose + /evolve/history
    # -----------------------------------------------------------------------
    @app.post("/evolve/propose")
    def evolve_propose(req: EvolveProposeReq = Body(...)):
        from monad.evolution import (
            EvolutionLog, EvolutionManager, EvolutionZone,
            PatchProposer, RollbackManager, SandboxRunner,
        )
        from monad.policy import PolicyGate
        try:
            zone = EvolutionZone(req.zone)
        except ValueError:
            raise HTTPException(400, f"unknown zone: {req.zone}")

        memory_dir = apporch.resources.memory_dir
        elog = EvolutionLog(memory_dir / "evolution.db")
        mgr = EvolutionManager(
            root=r,
            evolution_log=elog,
            proposer=PatchProposer(root=r),
            sandbox=SandboxRunner(root=r),
            rollback=RollbackManager(root=r,
                                      backups_dir=memory_dir / "evolution_backups"),
            policy_gate=PolicyGate(require_approval_for=["evolution.apply"]),
        )
        try:
            rec, proposal = mgr.propose(goal=req.goal, zone=zone,
                                        target_path=req.target)
        except PermissionError as e:
            raise HTTPException(403, str(e))

        return {
            "record_id": rec.id,
            "target": rec.target_path,
            "model_used": proposal.model_used,
            "rationale": proposal.rationale,
            "diff_preview": proposal.diff[:2000],
            "warnings": proposal.warnings,
        }

    @app.get("/evolve/history")
    def evolve_history(limit: int = 20):
        from monad.evolution import EvolutionLog
        elog = EvolutionLog(apporch.resources.memory_dir / "evolution.db")
        recs = elog.history(limit=limit)
        return {"records": [
            {"id": rc.id, "timestamp": rc.timestamp,
             "change_type": rc.change_type.value, "outcome": rc.outcome.value,
             "target": rc.target_path, "goal": rc.goal}
            for rc in recs
        ]}

    return app


def _guess_readme_url(repo_url: str) -> str:
    """Guess the raw README URL from a github-ish repo url."""
    import re
    m = re.match(r"https?://github\.com/([^/]+)/([^/.]+)(?:\.git)?/?", repo_url)
    if m:
        owner, repo = m.group(1), m.group(2)
        return f"https://raw.githubusercontent.com/{owner}/{repo}/main/README.md"
    return ""


def serve(host: str = "127.0.0.1", port: int = 8765,
          root: Path | None = None) -> None:
    """Run the server via uvicorn."""
    try:
        import uvicorn
    except ImportError as e:
        raise RuntimeError("uvicorn not installed — pip install 'uvicorn[standard]'") from e
    app = create_app(root=root)
    uvicorn.run(app, host=host, port=port, log_level="info")


# ---------------------------------------------------------------------------
# Self-contained dashboard (works in restricted preview iframes — inline only)
# ---------------------------------------------------------------------------

_DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Monad-Ultron Dashboard</title>
<style>
  body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
         background: #0f172a; color: #e2e8f0; margin: 0; padding: 2rem; }
  h1 { color: #a78bfa; margin-top: 0; }
  h2 { color: #60a5fa; border-bottom: 1px solid #334155; padding-bottom: 0.4rem; }
  .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
          gap: 1rem; margin-top: 1rem; }
  .card { background: #1e293b; padding: 1rem 1.2rem; border-radius: 0.5rem;
          border: 1px solid #334155; }
  .card h3 { margin-top: 0; color: #f472b6; }
  .badge { display: inline-block; padding: 0.15rem 0.5rem; border-radius: 0.3rem;
           background: #7c3aed; color: white; font-size: 0.8rem; margin-right: 0.4rem; }
  input, textarea, button { font: inherit; padding: 0.5rem; border-radius: 0.3rem;
           border: 1px solid #475569; background: #0f172a; color: #e2e8f0; }
  button { background: #7c3aed; cursor: pointer; border-color: #7c3aed; }
  button:hover { background: #8b5cf6; }
  textarea { width: 100%; min-height: 80px; }
  pre { background: #020617; padding: 0.7rem; border-radius: 0.3rem;
        white-space: pre-wrap; overflow-x: auto; font-size: 0.85rem; }
  .row { display: flex; gap: 0.5rem; margin: 0.5rem 0; }
  .row input, .row textarea { flex: 1; }
</style>
</head>
<body>
<h1>🧠 Monad-Ultron Dashboard <span class="badge">v{{VERSION}}</span></h1>
<p>Portable local AI orchestration platform · 82 cognitive organs · self-improving</p>

<div class="grid">
  <div class="card">
    <h3>System</h3>
    <button onclick="fetchTo('/info', 'info')">Refresh</button>
    <pre id="info">click Refresh</pre>
  </div>

  <div class="card">
    <h3>Ask Monad</h3>
    <div class="row"><textarea id="prompt" placeholder="Your question…"></textarea></div>
    <div class="row">
      <label><input type="checkbox" id="cognition"> cognition pre-pass</label>
      <button onclick="ask()">Send</button>
    </div>
    <pre id="answer">…</pre>
  </div>

  <div class="card">
    <h3>Memory</h3>
    <div class="row"><input id="mem_text" placeholder="text to remember or query">
      <button onclick="remember()">Remember</button>
      <button onclick="recall()">Recall</button></div>
    <pre id="mem_out">…</pre>
  </div>

  <div class="card">
    <h3>Organs (82)</h3>
    <button onclick="fetchTo('/organs', 'organs')">Load</button>
    <pre id="organs" style="max-height: 240px; overflow-y: auto">click Load</pre>
  </div>

  <div class="card">
    <h3>Tools</h3>
    <button onclick="fetchTo('/tools', 'tools')">List</button>
    <pre id="tools">click List</pre>
  </div>

  <div class="card">
    <h3>Policy Audit</h3>
    <button onclick="fetchTo('/policy/audit', 'audit')">Load</button>
    <pre id="audit">click Load</pre>
  </div>
</div>

<script>
async function fetchTo(url, elId) {
  const r = await fetch(url);
  const j = await r.json();
  document.getElementById(elId).textContent = JSON.stringify(j, null, 2);
}
async function ask() {
  const prompt = document.getElementById('prompt').value;
  const cognition = document.getElementById('cognition').checked;
  document.getElementById('answer').textContent = 'thinking…';
  const r = await fetch('/ask', {method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({prompt, cognition})});
  document.getElementById('answer').textContent = JSON.stringify(await r.json(), null, 2);
}
async function remember() {
  const text = document.getElementById('mem_text').value;
  const r = await fetch('/memory/remember', {method:'POST',
    headers:{'Content-Type':'application/json'}, body: JSON.stringify({text})});
  document.getElementById('mem_out').textContent = JSON.stringify(await r.json(), null, 2);
}
async function recall() {
  const query = document.getElementById('mem_text').value;
  const r = await fetch('/memory/recall', {method:'POST',
    headers:{'Content-Type':'application/json'}, body: JSON.stringify({query, top_k: 5})});
  document.getElementById('mem_out').textContent = JSON.stringify(await r.json(), null, 2);
}
</script>
</body>
</html>
"""
