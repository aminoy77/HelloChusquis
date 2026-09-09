import subprocess
import sys
from pathlib import Path
from rich.console import Console
from rich.panel import Panel

from core.plugins import validate_plugin_name, write_plugin_code

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
        choices = response.get("choices", [])
        if not choices:
            return ""
        code = choices[0].get("message", {}).get("content", "") or ""
        code = code.replace("```python", "").replace("```", "").strip()
        return code
    except Exception:
        return ""


def generate_plugin_code(topic: str, api_research: str, plugin_name: str, pool) -> str:
    """Generate a complete plugin implementation when an LLM provider is available."""
    if pool is None:
        return ""
    try:
        response = pool.chat_with_retry([
            {"role": "system", "content": BUILDER_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Build a plugin named {plugin_name!r} for: {topic}.\n\n"
                    f"Research notes:\n{api_research}\n\n"
                    "Return only complete Python source code."
                ),
            },
        ])
        choices = response.get("choices", [])
        code = choices[0].get("message", {}).get("content", "") if choices else ""
        return code.replace("```python", "").replace("```", "").strip()
    except Exception:
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
    console.print("  [dim]Attempting to fix plugin code...[/dim]")
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
        choices = response.get("choices", [])
        fixed_code = choices[0].get("message", {}).get("content", "") if choices else ""
        fixed_code = fixed_code.replace("```python", "").replace("```", "").strip()
        return fixed_code
    except Exception:
        return ""


def build_plugin(topic: str, plugin_name: str, pool) -> str:
    """Build a plugin through a validated, owner-only plugin path."""
    plugin_name = validate_plugin_name(plugin_name)
    plugin_path = PLUGINS_DIR / f"{plugin_name}.py"

    console.print(Panel(f"[bold green]Building new plugin: {plugin_name}[/bold green]", expand=False))

    # 1. Investigación de API
    api_research = research_api(topic, pool)
    if not api_research or "Could not research API" in (api_research or ""):
        console.print("[yellow]Could not research API. Proceeding with basic template...[/yellow]")
        api_research = """API: Generic REST API
Base URL: https://api.example.com/v1
Auth: Bearer token
Key endpoints:
- GET /items - List items
- POST /items - Create item
"""
    console.print("  [dim]API Research complete.[/dim]")

    # 2. Generación de código
    plugin_code = generate_plugin_code(topic, api_research, plugin_name, pool)
    if not plugin_code:
        console.print("[yellow]Generating basic WhatsApp plugin...[/yellow]")
        plugin_code = generate_basic_whatsapp_plugin(plugin_name, topic)

    # 3. Guardar y probar (con reintentos de arreglo)
    attempts = 0
    max_attempts = 3
    while attempts < max_attempts:
        plugin_path = write_plugin_code(plugin_name, plugin_code)
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
    console.print(f"Plugin saved to: {plugin_path}")
    console.print("\n[dim]To add to registry, run:[/dim]")
    console.print("[cyan]  hellochusquis build[/cyan]")
    console.print("[dim]and answer 'y' to the registry question.[/dim]")
    return f"Plugin '{plugin_name}' built successfully! Saved to {plugin_path}"


if __name__ == '__main__':
    pass


def generate_basic_whatsapp_plugin(plugin_name: str, topic: str) -> str:
    """Generate a basic WhatsApp plugin when API research fails."""
    name = plugin_name.replace("_", " ").title()
    return f'''"""HelloChusquis Plugin: {name}"""

PLUGIN_NAME = "{plugin_name}"
PLUGIN_DESCRIPTION = "{topic}"
PLUGIN_VERSION = "1.0.0"
PLUGIN_AUTHOR = "HelloChusquis Builder"

PLUGIN_SCHEMA = {{
    "type": "function",
    "function": {{
        "name": "{plugin_name}",
        "description": "{topic}",
        "parameters": {{
            "type": "object",
            "properties": {{
                "phone": {{"type": "string", "description": "Recipient phone number with country code"}},
                "message": {{"type": "string", "description": "Message text to send"}},
                "token": {{"type": "string", "description": "WhatsApp Business API token"}},
                "phone_id": {{"type": "string", "description": "WhatsApp Business Phone ID"}}
            }},
            "required": ["phone", "message", "token", "phone_id"]
        }}
    }}
}}


def run(phone: str, message: str, token: str, phone_id: str) -> str:
    """Send WhatsApp message via Meta Graph API."""
    import httpx
    
    url = f"https://graph.facebook.com/v18.0/{{phone_id}}/messages"
    headers = {{"Authorization": f"Bearer {{token}}", "Content-Type": "application/json"}}
    payload = {{
        "messaging_product": "whatsapp",
        "to": phone,
        "type": "text",
        "text": {{"body": message}}
    }}
    
    try:
        with httpx.Client() as client:
            response = client.post(url, json=payload, headers=headers, timeout=30)
            result = response.json()
            if response.status_code == 200:
                return f"Message sent! ID: {{result.get('messages', [{{}}])[0].get('id', 'N/A')}}"
            else:
                return f"Error: {{result.get('error', {{}}).get('message', 'Unknown error')}}"
    except Exception as e:
        return f"Error: {{str(e)}}"


if __name__ == "__main__":
    print("WhatsApp Auto Messenger Plugin")
    print("Requirements:")
    print("1. Meta Business App with WhatsApp product")
    print("2. WhatsApp Business Phone Number")
    print("3. Permanent User Access Token")
    print()
    print("Run: hellochusquis")
'''
