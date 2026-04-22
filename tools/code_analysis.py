from tools.base import BaseTool, ToolResult


PLUGIN_NAME = "code_analysis"
PLUGIN_DESCRIPTION = "Analyze and format code with linters and formatters"

CODE_ANALYSIS_SCHEMA = {
    "type": "function",
    "function": {
        "name": "code_analysis",
        "description": "Run code analysis, linting, and formatting",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["lint", "format", "check", "fix"],
                    "description": "Code analysis action"
                },
                "tool": {
                    "type": "string",
                    "enum": ["eslint", "black", "ruff", "mypy", "prettier", "prettier"],
                    "description": "Tool to use"
                },
                "path": {"type": "string", "description": "File or directory path"},
                "fix": {"type": "boolean", "description": "Auto-fix issues"},
            },
            "required": ["action", "tool", "path"]
        }
    }
}


def run(action: str, tool: str, path: str, fix: bool = False) -> str:
    """Run code analysis tools."""
    import subprocess
    import os
    
    if not path:
        return "Error: path required"
    
    if not os.path.exists(path):
        return f"Error: Path not found: {path}"
    
    try:
        if action == "lint" or action == "check":
            if tool == "eslint":
                cmd = ["npx", "eslint", path, "--format", "stylish"]
            elif tool == "ruff":
                cmd = ["ruff", "check", path]
            elif tool == "mypy":
                cmd = ["mypy", path]
            elif tool == "black":
                cmd = ["black", "--check", path]
            else:
                return f"Error: Unknown tool {tool}"
                
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
                return f"✓ {tool} found no issues in {path}"
            return result.stdout + result.stderr
        
        elif action == "format":
            if tool == "black":
                cmd = ["black", path]
            elif tool == "ruff":
                cmd = ["ruff", "format", path]
            elif tool == "prettier":
                cmd = ["npx", "prettier", "--write", path]
            else:
                return f"Error: Unknown tool {tool}"
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
                return f"✓ Formatted {path} with {tool}"
            return result.stdout + result.stderr
        
        elif action == "fix":
            if tool == "ruff":
                cmd = ["ruff", "check", "--fix", path]
            elif tool == "eslint":
                cmd = ["npx", "eslint", "--fix", path]
            else:
                return f"Error: {tool} does not support auto-fix"
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            return f"✓ Auto-fixed with {tool}\n{result.stdout}"
        
        else:
            return f"Error: Unknown action {action}"
    
    except FileNotFoundError:
        return f"Error: {tool} not installed. Run: pip install ruff (or npm install -g eslint)"
    except Exception as e:
        return f"Error: {str(e)}"


if __name__ == "__main__":
    print("Code Analysis plugin loaded.")