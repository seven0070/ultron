"""
HTTPTool — network fetch via stdlib urllib.

Restrictions:
  - only http(s) schemes
  - deny-list for localhost, RFC1918 private ranges by default (SSRF protection)
  - max response size
  - hard timeout
"""

from __future__ import annotations

import ipaddress
import socket
import urllib.parse
import urllib.request

from monad.tools.base import Tool, ToolResult


class HTTPTool(Tool):
    id = "http"
    name = "HTTP Fetch"
    description = "GET a URL with SSRF protections and size cap"
    requires_approval = True
    action = "net"

    DEFAULT_TIMEOUT_S = 15
    MAX_BYTES = 2 * 1024 * 1024      # 2 MB
    BLOCKED_HOSTS = {"localhost", "127.0.0.1", "0.0.0.0", "::1"}

    def __init__(self, allow_private: bool = False) -> None:
        self.allow_private = allow_private

    def invoke(self, url: str = "", method: str = "GET",
               timeout_s: float | None = None, headers: dict | None = None,
               **kwargs) -> ToolResult:
        if not url:
            return ToolResult(tool=self.id, ok=False, error="missing url")
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return ToolResult(tool=self.id, ok=False,
                              error=f"only http(s) allowed, got {parsed.scheme!r}")
        host = parsed.hostname or ""
        if not host:
            return ToolResult(tool=self.id, ok=False, error="no host in URL")
        if not self.allow_private and self._is_blocked_host(host):
            return ToolResult(tool=self.id, ok=False,
                              error=f"blocked host (SSRF protection): {host}")

        t = float(timeout_s or self.DEFAULT_TIMEOUT_S)
        req = urllib.request.Request(url, method=method.upper())
        for k, v in (headers or {}).items():
            req.add_header(k, v)
        req.add_header("User-Agent", "Monad-Ultron/0.5 (+https://github.com/monad)")

        try:
            with urllib.request.urlopen(req, timeout=t) as resp:
                body = resp.read(self.MAX_BYTES + 1)
                truncated = len(body) > self.MAX_BYTES
                body = body[:self.MAX_BYTES]
                try:
                    text = body.decode("utf-8", errors="replace")
                except Exception:
                    text = ""
                return ToolResult(
                    tool=self.id, ok=(200 <= resp.status < 400),
                    output={"status": resp.status, "text": text,
                            "truncated": truncated, "bytes": len(body)},
                    metadata={"url": url,
                              "content_type": resp.headers.get("Content-Type", ""),
                              "timeout_s": t},
                )
        except Exception as e:
            return ToolResult(tool=self.id, ok=False, error=f"fetch failed: {e}")

    # -- SSRF check -----------------------------------------------------------

    def _is_blocked_host(self, host: str) -> bool:
        if host.lower() in self.BLOCKED_HOSTS:
            return True
        # Resolve; block private/loopback/reserved
        try:
            infos = socket.getaddrinfo(host, None)
            for family, _, _, _, addr in infos:
                ip_str = addr[0]
                try:
                    ip = ipaddress.ip_address(ip_str)
                except ValueError:
                    continue
                if ip.is_private or ip.is_loopback or ip.is_reserved or ip.is_link_local:
                    return True
        except socket.gaierror:
            return True   # can't resolve → refuse
        return False
