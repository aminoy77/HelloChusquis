from tools.base import BaseTool, ToolResult
import subprocess
import tempfile
import os


class CodeTool(BaseTool):
    name = "code"
    description = "Execute Python code and return output"

    def run(self, code: str) -> ToolResult:
        if not code or not code.strip():
            return ToolResult(success=False, output="", error="No code provided")

        try:
            # Write code to temp file for better error messages
            with tempfile.NamedTemporaryFile(
                mode='w', suffix='.py', delete=False, encoding='utf-8'
            ) as f:
                f.write(code)
                tmp_path = f.name

            try:
                result = subprocess.run(
                    ["python3", tmp_path],
                    capture_output=True,
                    text=True,
                    timeout=30,
                    env={**os.environ, 'PYTHONIOENCODING': 'utf-8'}
                )

                output = result.stdout
                error = result.stderr

                if result.returncode == 0:
                    if output:
                        return ToolResult(success=True, output=output.rstrip())
                    return ToolResult(success=True, output="Code executed successfully (no output)")
                else:
                    # Clean up traceback to show relevant info
                    if error:
                        # Get last meaningful lines of traceback
                        lines = error.strip().split('\n')
                        if len(lines) > 5:
                            error = '\n'.join(lines[-5:])
                    return ToolResult(success=False, output=output, error=error)

            finally:
                os.unlink(tmp_path)

        except subprocess.TimeoutExpired:
            return ToolResult(success=False, output="", error="Code execution timed out after 30 seconds")
        except Exception as e:
            return ToolResult(success=False, output="", error=f"Execution error: {e}")
