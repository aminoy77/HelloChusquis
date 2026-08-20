"""A bounded, approval-gated Python execution helper."""

import os
import signal
import subprocess
import tempfile
import threading
from pathlib import Path

from tools.base import BaseTool, ToolResult


class CodeTool(BaseTool):
    name = "code"
    description = "Execute Python code and return bounded output"
    MAX_CODE_CHARS = 100_000
    MAX_OUTPUT_CHARS = 65_536
    TIMEOUT_SECONDS = 30
    _TRUNCATION_MARKER = "\n[output truncated]"

    @classmethod
    def _collect_stream(cls, stream, target: bytearray, truncated: list[bool]) -> None:
        """Drain a process stream without retaining more than the configured limit."""
        retained_limit = cls.MAX_OUTPUT_CHARS - len(cls._TRUNCATION_MARKER.encode("utf-8"))
        while chunk := stream.read(8192):
            remaining = retained_limit - len(target)
            if remaining > 0:
                target.extend(chunk[:remaining])
            if len(chunk) > max(remaining, 0):
                truncated[0] = True

    @classmethod
    def _format_stream(cls, value: bytearray, was_truncated: bool) -> str:
        text = value.decode("utf-8", errors="replace")
        if was_truncated:
            text += cls._TRUNCATION_MARKER
        return text

    @staticmethod
    def _safe_environment() -> dict[str, str]:
        """Return the small runtime environment needed by the Python interpreter."""
        environment = {
            "PATH": os.environ.get("PATH", "/usr/local/bin:/usr/bin:/bin"),
            "PYTHONIOENCODING": "utf-8",
            "PYTHONUNBUFFERED": "1",
        }
        for name in ("LANG", "LC_ALL", "TZ"):
            if value := os.environ.get(name):
                environment[name] = value
        return environment

    def run(self, code: str) -> ToolResult:
        if not isinstance(code, str) or not code.strip():
            return ToolResult(success=False, output="", error="No code provided")
        if len(code) > self.MAX_CODE_CHARS:
            return ToolResult(
                success=False,
                output="",
                error=f"Code exceeds the {self.MAX_CODE_CHARS}-character limit",
            )

        tmp_path: str | None = None
        process: subprocess.Popen | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".py", delete=False, encoding="utf-8"
            ) as handle:
                handle.write(code)
                handle.flush()
                os.fchmod(handle.fileno(), 0o600)
                tmp_path = handle.name

            process = subprocess.Popen(
                ["python3", "-I", tmp_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.DEVNULL,
                text=False,
                cwd=tempfile.gettempdir(),
                env=self._safe_environment(),
                start_new_session=True,
            )
            stdout, stderr = bytearray(), bytearray()
            stdout_truncated, stderr_truncated = [False], [False]
            stdout_reader = threading.Thread(
                target=self._collect_stream,
                args=(process.stdout, stdout, stdout_truncated),
                daemon=True,
            )
            stderr_reader = threading.Thread(
                target=self._collect_stream,
                args=(process.stderr, stderr, stderr_truncated),
                daemon=True,
            )
            stdout_reader.start()
            stderr_reader.start()
            try:
                returncode = process.wait(timeout=self.TIMEOUT_SECONDS)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
                stdout_reader.join()
                stderr_reader.join()
                return ToolResult(
                    success=False,
                    output="",
                    error=f"Code execution timed out after {self.TIMEOUT_SECONDS} seconds",
                )
            stdout_reader.join()
            stderr_reader.join()

            output = self._format_stream(stdout, stdout_truncated[0]).rstrip()
            error = self._format_stream(stderr, stderr_truncated[0]).rstrip()
            if returncode == 0:
                return ToolResult(
                    success=True,
                    output=output or "Code executed successfully (no output)",
                )
            return ToolResult(success=False, output=output, error=error or "Code execution failed")
        except OSError:
            return ToolResult(success=False, output="", error="Code execution unavailable")
        finally:
            if process is not None:
                for stream in (process.stdout, process.stderr):
                    if stream is not None:
                        stream.close()
            if tmp_path is not None:
                try:
                    Path(tmp_path).unlink()
                except FileNotFoundError:
                    pass
