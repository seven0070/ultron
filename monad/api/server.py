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
    AskReq = RememberReq = RecallReq = ToolInvokeReq = None  # type: ignore


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

    return app


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
