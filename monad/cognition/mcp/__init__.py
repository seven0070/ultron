"""
MCP (Model Context Protocol) layer.

Two directions:
  1. EXPORT   — expose Monad's organs as MCP tools for external clients
  2. IMPORT   — consume external MCP servers as first-class tools

The real `mcp` Python SDK is optional. When absent, we ship a self-contained
in-process fake that mirrors the JSON-RPC surface enough to test integration
end-to-end.
"""

from monad.cognition.mcp.bridge import MCPBridge, MCPTool, MonadMCPServer

__all__ = ["MCPBridge", "MCPTool", "MonadMCPServer"]
