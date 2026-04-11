import json
import subprocess
import sys
from pathlib import Path
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.syntax import Syntax

console = Console()
PLUGINS_DIR = Path.home() / ".hellochusquis" / "plugins"


BUILDER_SYSTEM_PROMPT = """You are an expert Python plugin developer for HelloChusquis AI agent.

Your job is to write a complete, working Python plugin file.

PLUGIN STRUCTURE (mandatory):
```python
PLUGIN_NAME = "pluginname"  # lowercase, no spaces
PLUGIN_DESCRIPTION = "What this plugin does"
PLUGIN_SCHEMA = {
    "type": "function",
    "function": {
        "name": "pluginname",
        "description": PLUGIN_DESCRIPTION,
        "parameters": {
            "type": "object",
            "properties": {
                "param1": {"type": "string", "description": "..."}
            },
            "required": ["param1"]
        }
    }
}

def run(param1: str) -> str:
    # Your implementation here
    return "result"
```

RULES:
- Only use stdlib or pip-installable packages
- Add pip install instructions as a comment at the top if needed
- Handle all exceptions gracefully, return error strings instead of raising
- Test with realistic inputs
- The run() function must always return a string
- Research the real API endpoints and use them

Respond with ONLY the Python code, no explanation, no markdown backticks.
"""


def research_api(topic: str, pool) -> str:
    """Usa el LLM con web search para investigar la API."""
    console.print(f"  [dim]Researching {topic} API...[/dim]")
    try:
        response = pool.chat_with_retry([
            {
                "role": "system",
                "content": (
                    "You are a technical researcher. "
                    "Research how to connect to and control the requested device or service via API. "
                    "Find: API endpoints, authentication method, required parameters, Python libraries available. "
                    "Be specific and practical. Include real endpoint URLs if available."
                )
            },
            {
                "role": "user",
                "content": f"Research: How to control/connect to {topic} via Python API or library. Find official API docs, endpoints, auth method, and best Python library to use."
            }
        ], tools=[{
            "type": "function",
            "function": {
                "name": "web_search",
                "description": "Search the web",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"}
                    },
                    "required": ["query"]
                }
            }
        }])
        content = response["choices"][0]["message"].get("content", "")
        return content
    except Exception as e:
        return f"Could not research API: {e}"


def generate_plugin_code(topic: str, research: str, plugin_name: str, pool) -> str:
    """Genera el código del plugin basado en la investigación."""
    console.print(f"  [dim]Generating plugin code...[/dim]")
    try:
        response = pool.chat_with_retry([
            {"role": "system", "content": BUILDER_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Create a HelloChusquis plugin for: {topic}\n\n"
                    f"Plugin name: {plugin_name}\n\n"
                    f"API Research:\n{research}\n\n"
                    "Write the complete plugin code now."
                )
            }
        ])
        code = response["choices"][0]["message"].get("content", "")
        # Limpia backticks si los hay
        code = code.replace("```python", "").replace("```", "").strip()
        return code
    except Exception as e:
        return ""


def test_plugin(plugin_path: Path) -> tuple[bool, str]:
    """Intenta importar el plugin y verificar su estructura."""
    try:
        result = subprocess.run(
            [sys.executable, "-c", f"""
import importlib.util
spec = importlib.util.spec_from_file_location("test_plugin", "{plugin_path}")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
required = ["PLUGIN_NAME", "PLUGIN_SCHEMA", "run"]
missing = [r for r in required if not hasattr(mod, r)]
if missing:
    print(f"MISSING: {{missing}}")
else:
    print(f"OK: {{mod.PLUGIN_NAME}}")
"""],
            capture_output=True, text=True, timeout=15
        )
        output = result.stdout.strip()
        if output.startswith("OK:"):
            return True, output
        else:
            return False, result.stdout + result.stderr
    except Exception as e:
        return False, str(e)


def fix_plugin_code(code: str, error: str, pool) -> str:
    """Intenta arreglar el código del plugin con la ayuda del LLM."""
    console.print(f"  [dim]Attempting to fix plugin code...[/dim]")
    try:
        response = pool.chat_with_retry([
            {"role": "system", "content": BUILDER_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"The following plugin code has an error:\n\n"
                    f"```python\n{code}\n```\n\n"
                    f"Error details:\n{error}\n\n"
                    "Please provide the corrected and complete plugin code. "
                    "Respond with ONLY the Python code, no explanation, no markdown backticks."
                )
            }
        ])
        fixed_code = response["choices"][0]["message"].get("content", "")
        fixed_code = fixed_code.replace("```python", "").replace("```", "").strip()
        return fixed_code
    except Exception as e:
        return ""


def build_plugin(topic: str, plugin_name: str, pool) -> str:
    """Flujo completo para construir un plugin."""
    PLUGINS_DIR.mkdir(parents=True, exist_ok=True)
    plugin_path = PLUGINS_DIR / f"{plugin_name}.py"

    console.print(Panel(f"[bold green]Building new plugin: {plugin_name}[/bold green]", expand=False))

    # 1. Investigación de API
    api_research = research_api(topic, pool)
    if "Could not research API" in api_research:
        return f"Error during API research: {api_research}"
    console.print(f"  [dim]API Research complete.[/dim]")

    # 2. Generación de código
    plugin_code = generate_plugin_code(topic, api_research, plugin_name, pool)
    if not plugin_code:
        return "Error: Could not generate plugin code."

    # 3. Guardar y probar (con reintentos de arreglo)
    attempts = 0
    max_attempts = 3
    while attempts < max_attempts:
        plugin_path.write_text(plugin_code)
        console.print(f"  [dim]Plugin code saved to {plugin_path}. Testing...[/dim]")
        is_valid, test_output = test_plugin(plugin_path)

        if is_valid:
            console.print(f"  [green]Plugin {plugin_name} is valid![/green]")
            break
        else:
            console.print(f"  [yellow]Plugin test failed (attempt {attempts + 1}/{max_attempts}):[/yellow]\n{test_output}")
            if attempts < max_attempts - 1:
                plugin_code = fix_plugin_code(plugin_code, test_output, pool)
                if not plugin_code:
                    return "Error: Could not fix plugin code."
            attempts += 1
    else:
        return f"Error: Plugin {plugin_name} failed to pass tests after {max_attempts} attempts. Check {plugin_path} for details."

    # 4. Preguntar si subir al registry
    console.print(Panel(f"[bold green]Plugin {plugin_name} built and tested successfully![/bold green]", expand=False))
    if Confirm.ask("Do you want to add this plugin to the HelloChusquis registry on GitHub? (This will generate instructions for a Pull Request)", default=False):
        # Generar instrucciones para PR
        pr_instructions = f"""
        To add '{plugin_name}' to the official HelloChusquis-Plugins registry, follow these steps:

        1.  **Fork** the repository: [https://github.com/aminoy77/HelloChusquis-plugins](https://github.com/aminoy77/HelloChusquis-plugins)
        2.  **Clone** your forked repository to your local machine.
        3.  **Copy** the generated plugin file '{plugin_name}.py' from '~/.hellochusquis/plugins/' to the 'plugins/' directory in your cloned repository.
        4.  **Edit** 'registry.json' to add a new entry for '{plugin_name}':
            ```json
            """{plugin_name}": {
                "url": "https://raw.githubusercontent.com/<YOUR_GITHUB_USERNAME>/HelloChusquis-plugins/main/plugins/{plugin_name}.py",
                "description": "{PLUGIN_DESCRIPTION_FROM_PLUGIN_FILE}", # Get this from the plugin file
                "author": "<YOUR_NAME_OR_GITHUB_USERNAME>"
            }"""
            (Remember to replace `<YOUR_GITHUB_USERNAME>` and `<YOUR_NAME_OR_GITHUB_USERNAME>`)
        5.  **Commit** your changes and **Push** to your forked repository.
        6.  Open a **Pull Request** from your forked repository to the main 'aminoy77/HelloChusquis-plugins' repository.

        Thank you for your contribution!
        """
        return f"Plugin '{plugin_name}' built. \n\n{pr_instructions}"
    else:
        return f"Plugin '{plugin_name}' built and saved locally at {plugin_path}. Not added to registry."


if __name__ == '__main__':
    # Example usage (for testing purposes)
    # This part would typically be called by the agent
    # from core.agent import agent_pool
    # build_plugin("control Govee LED lights", "govee_lights", agent_pool)
    pass
