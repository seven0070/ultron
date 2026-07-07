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
