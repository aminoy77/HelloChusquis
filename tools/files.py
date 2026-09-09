from tools.base import BaseTool, ToolResult
from pathlib import Path


class FilesTool(BaseTool):
    name = "files"
    description = "Read, write, create, delete, and list files"

    def __init__(self, allowed_dirs: list[str]):
        self.allowed_dirs = [Path(d).expanduser().resolve() for d in allowed_dirs]

    def _is_allowed(self, path: Path) -> bool:
        path = path.expanduser().resolve()
        return any(
            path == allowed or allowed in path.parents
            for allowed in self.allowed_dirs
        )

    def _deny(self, path: str) -> ToolResult:
        return ToolResult(
            success=False,
            output="",
            error=f"Access denied: '{path}' is outside allowed directories."
        )

    def run(self, action: str, path: str, content: str = "") -> ToolResult:
        p = Path(path).expanduser().resolve()

        if not self._is_allowed(p):
            return self._deny(path)

        try:
            if action == "read":
                if not p.exists():
                    return ToolResult(success=False, output="", error=f"File not found: {p}")
                return ToolResult(success=True, output=p.read_text(encoding="utf-8"))

            elif action == "write":
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(content, encoding="utf-8")
                # Verify write succeeded
                if not p.exists():
                    return ToolResult(success=False, output="", error=f"Failed to verify file creation: {p}")
                size = p.stat().st_size
                return ToolResult(success=True, output=f"File created: {p} ({size} bytes)")

            elif action == "delete":
                if not p.exists():
                    return ToolResult(success=False, output="", error=f"File not found: {p}")
                p.unlink()
                return ToolResult(success=True, output=f"Deleted: {p}")

            elif action == "list":
                if not p.exists():
                    return ToolResult(success=False, output="", error=f"Directory not found: {p}")
                entries = sorted(p.iterdir(), key=lambda x: (x.is_file(), x.name))
                lines = [
                    f"{'DIR ' if e.is_dir() else 'FILE'} {e.name}"
                    for e in entries
                ]
                return ToolResult(success=True, output="\n".join(lines))

            elif action == "create_dir":
                p.mkdir(parents=True, exist_ok=True)
                return ToolResult(success=True, output=f"Directory created: {p}")

            else:
                return ToolResult(success=False, output="", error=f"Unknown action: {action}. Use: read, write, delete, list, create_dir")

        except Exception as e:
            return ToolResult(success=False, output="", error=f"Error: {e}")

    def allow_dir(self, path: str):
        resolved = Path(path).expanduser().resolve()
        if resolved not in self.allowed_dirs:
            self.allowed_dirs.append(resolved)
