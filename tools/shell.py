from tools.base import BaseTool, ToolResult
import subprocess


class ShellTool(BaseTool):
    name = "shell"
    description = "Ejecuta comandos en la terminal del sistema"

    def run(self, command: str) -> ToolResult:
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                return ToolResult(success=True, output=result.stdout)
            return ToolResult(success=False, output=result.stdout, error=result.stderr)
        except subprocess.TimeoutExpired:
            return ToolResult(success=False, output="", error="Command timed out after 30s")