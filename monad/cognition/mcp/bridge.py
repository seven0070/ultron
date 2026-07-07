"""MCP export/import bridge (SDK-optional)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

try:
    import mcp                               # type: ignore
    HAVE_MCP = True
except Exception:
    HAVE_MCP = False


@dataclass
class MCPTool:
    name: str
    description: str
    handler: Callable[[dict], Any]
    schema: dict = field(default_factory=dict)


class MCPBridge:
    """
    - register_organ_as_tool(organ)   → export
    - add_external_tool(name, ...)    → import
    - list_tools()                    → all known tools
    - invoke(name, payload)           → call any tool uniformly
    """

    def __init__(self) -> None:
        self._tools: dict[str, MCPTool] = {}

    # -- export ---------------------------------------------------------------

    def register_organ_as_tool(self, organ) -> MCPTool:
        def handler(payload: dict) -> Any:
            prompt = payload.get("prompt") or payload.get("input") or ""
            return organ.process(prompt, context=payload).__dict__

        tool = MCPTool(
            name=f"organ.{organ.name}",
            description=organ.description,
            handler=handler,
            schema={"type": "object",
                    "properties": {"prompt": {"type": "string"}},
                    "required": ["prompt"]},
        )
        self._tools[tool.name] = tool
        return tool

    # -- import ---------------------------------------------------------------

    def add_external_tool(self, name: str, description: str,
                          handler: Callable[[dict], Any],
                          schema: dict | None = None) -> MCPTool:
        tool = MCPTool(name=name, description=description, handler=handler,
                       schema=schema or {})
        self._tools[name] = tool
        return tool

    # -- listing & invocation -------------------------------------------------

    def list_tools(self) -> list[dict]:
        return [{"name": t.name, "description": t.description, "schema": t.schema}
                for t in self._tools.values()]

    def invoke(self, name: str, payload: dict) -> Any:
        if name not in self._tools:
            raise KeyError(f"Unknown MCP tool: {name}")
        return self._tools[name].handler(payload)

    @property
    def sdk_available(self) -> bool:
        return HAVE_MCP


# ---------------------------------------------------------------------------
# MonadMCPServer — from the Cognitive Architecture spec
# ---------------------------------------------------------------------------

class MonadMCPServer(MCPBridge):
    """MCP server exposing 3 default Monad-level tools:

        monad_recall            — query persistent memory
        monad_organ_analyze     — run a cognitive organ on a context
        monad_self_model_query  — query the self-model graph

    Plus every organ is available as `organ.<Name>` (from parent MCPBridge).
    """

    def __init__(self, monad_instance=None) -> None:
        super().__init__()
        self.name = "monad"
        self.monad = monad_instance

        self.add_external_tool(
            "monad_recall",
            "Query Monad's persistent memory (Cognee-backed)",
            self._recall,
            schema={"type": "object",
                    "properties": {"query": {"type": "string"},
                                   "mode": {"type": "string"}},
                    "required": ["query"]},
        )
        self.add_external_tool(
            "monad_organ_analyze",
            "Run a specific cognitive organ on given context",
            self._organ_analyze,
            schema={"type": "object",
                    "properties": {"organ": {"type": "string"},
                                   "context": {"type": "string"}},
                    "required": ["organ", "context"]},
        )
        self.add_external_tool(
            "monad_self_model_query",
            "Query the metacognitive self-model graph",
            self._self_model_query,
            schema={"type": "object",
                    "properties": {"question": {"type": "string"}},
                    "required": ["question"]},
        )

    def _recall(self, payload: dict) -> dict:
        query = payload.get("query", "")
        mode = payload.get("mode", "hybrid")
        if self.monad is None or getattr(self.monad, "memory", None) is None:
            return {"tool": "monad_recall", "query": query, "mode": mode,
                    "results": [], "note": "no monad instance bound"}
        hits = self.monad.memory.recall(query, mode=mode, top_k=5)
        return {"tool": "monad_recall", "query": query, "mode": mode, "results": hits}

    def _organ_analyze(self, payload: dict) -> dict:
        organ_name = payload.get("organ", "")
        context = payload.get("context", "")
        if self.monad is None or getattr(self.monad, "organs", None) is None:
            return {"tool": "monad_organ_analyze", "error": "no monad instance bound"}
        try:
            organ = self.monad.organs.get(organ_name)
        except KeyError:
            return {"tool": "monad_organ_analyze", "error": f"unknown organ: {organ_name}"}
        result = organ.process(context)
        return {"tool": "monad_organ_analyze", "organ": organ_name,
                "result": result.__dict__}

    def _self_model_query(self, payload: dict) -> dict:
        question = payload.get("question", "")
        if self.monad is None or getattr(self.monad, "self_model", None) is None:
            return {"tool": "monad_self_model_query", "error": "no monad instance bound"}
        return {"tool": "monad_self_model_query", "question": question,
                "stats": self.monad.self_model.stats(),
                "beliefs": [n.label for n in self.monad.self_model.by_kind("belief")]}
