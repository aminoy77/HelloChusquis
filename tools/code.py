from tools.base import BaseTool, ToolResult
import subprocess


class CodeTool(BaseTool):
    name = "code"
    description = "Ejecuta código Python"

    def run(self, code: str) -> ToolResult:
        try:
            result = subprocess.run(["python3", "-c", code], capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                return ToolResult(success=True, output=result.stdout)
            return ToolResult(success=False, output=result.stdout, error=result.stderr)
        except subprocess.TimeoutExpired:
            return ToolResult(success=False, output="", error="Command timed out after 30s")