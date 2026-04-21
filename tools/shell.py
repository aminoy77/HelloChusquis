from tools.base import BaseTool, ToolResult
import subprocess
import asyncio


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

    async def arun(self, command: str) -> ToolResult:
        """Versión asíncrona del comando shell."""
        try:
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)
            stdout_str = stdout.decode() if stdout else ""
            stderr_str = stderr.decode() if stderr else ""

            if proc.returncode == 0:
                return ToolResult(success=True, output=stdout_str)
            return ToolResult(success=False, output=stdout_str, error=stderr_str)
        except asyncio.TimeoutError:
            return ToolResult(success=False, output="", error="Command timed out after 30s")
        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))
