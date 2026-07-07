"""
FilesystemTool — read/write/list/delete files, sandboxed to workspace/.

Refuses paths that escape the sandbox via '..' or symlinks resolving outside.
"""

from __future__ import annotations

from pathlib import Path

from monad.tools.base import Tool, ToolError, ToolResult


class FilesystemTool(Tool):
    id = "filesystem"
    name = "Filesystem"
    description = "Sandboxed filesystem access — read, write, list, delete inside workspace/"
    requires_approval = True
    action = "fs"

    def __init__(self, workspace_dir: str | Path | None = None) -> None:
        self.workspace = Path(workspace_dir or "workspace").resolve()
        self.workspace.mkdir(parents=True, exist_ok=True)

    def invoke(self, op: str = "list", path: str = "", content: str = "",
               **kwargs) -> ToolResult:
        try:
            target = self._resolve(path)
        except ToolError as e:
            return ToolResult(tool=self.id, ok=False, error=str(e))

        if op == "list":
            return self._list(target)
        if op == "read":
            return self._read(target)
        if op == "write":
            return self._write(target, content)
        if op == "delete":
            return self._delete(target)
        if op == "mkdir":
            target.mkdir(parents=True, exist_ok=True)
            return ToolResult(tool=self.id, ok=True, output=f"created {target}")
        return ToolResult(tool=self.id, ok=False,
                          error=f"unknown op: {op} (want list|read|write|delete|mkdir)")

    # -- ops ------------------------------------------------------------------

    def _list(self, target: Path) -> ToolResult:
        if not target.exists():
            return ToolResult(tool=self.id, ok=False, error=f"not found: {target}")
        if target.is_file():
            return ToolResult(tool=self.id, ok=True,
                              output={"path": str(target), "size": target.stat().st_size})
        entries = []
        for p in sorted(target.iterdir()):
            entries.append({
                "name": p.name,
                "is_dir": p.is_dir(),
                "size": p.stat().st_size if p.is_file() else None,
            })
        return ToolResult(tool=self.id, ok=True,
                          output={"path": str(target), "entries": entries})

    def _read(self, target: Path) -> ToolResult:
        if not target.is_file():
            return ToolResult(tool=self.id, ok=False, error=f"not a file: {target}")
        if target.stat().st_size > 5 * 1024 * 1024:
            return ToolResult(tool=self.id, ok=False,
                              error="file exceeds 5 MB read limit")
        try:
            data = target.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return ToolResult(tool=self.id, ok=False, error="not a text file")
        return ToolResult(tool=self.id, ok=True,
                          output=data,
                          metadata={"path": str(target), "bytes": len(data)})

    def _write(self, target: Path, content: str) -> ToolResult:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return ToolResult(tool=self.id, ok=True,
                          output={"path": str(target), "written": len(content)})

    def _delete(self, target: Path) -> ToolResult:
        if not target.exists():
            return ToolResult(tool=self.id, ok=False, error=f"not found: {target}")
        if target.is_dir():
            # Refuse recursive deletes as a safety measure
            try:
                target.rmdir()
            except OSError:
                return ToolResult(tool=self.id, ok=False,
                                  error="directory not empty (recursive delete refused)")
        else:
            target.unlink()
        return ToolResult(tool=self.id, ok=True, output=f"deleted {target}")

    # -- sandbox --------------------------------------------------------------

    def _resolve(self, path: str) -> Path:
        p = (self.workspace / path).resolve() if path else self.workspace
        # Ensure resolved path is inside the workspace
        try:
            p.relative_to(self.workspace)
        except ValueError:
            raise ToolError(f"path escapes workspace: {path!r}")
        return p
