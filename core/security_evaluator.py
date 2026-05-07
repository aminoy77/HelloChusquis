import json
from typing import Dict, Optional
from rich.console import Console
console = Console()


HIGH_RISK_COMMANDS = {
    "rm": ["rf", "fr", "*", "-rf", "-fr"],
    "mv": ["/dev/null"],
    "chmod": [],
    ">": ["/dev/sda*"]
}


def evaluate_command_safety(command: str, pool) -> Dict:
    """Evalúa el riesgo potencial de un comando antes de ejecutarlo."""

    parts = command.strip().split()
    if not parts:
        return {"safe": True, "risk_level": "none"}

    cmd = parts[0]

    # Comprobamos contra lista conocida de comandos peligrosos
    risks = HIGH_RISK_COMMANDS.get(cmd, [])

    # Si no se encontró nada crítico explícitamente...
    if not risks and cmd not in HIGH_RISK_COMMANDS:
        return {"safe": True, "risk_level": "low", "reason": "Not recognized as high-risk"}

    # Enviar consulta al modelo LLM para análisis dinámico
    try:
        prompt = f"""
You're acting as a safety filter. A user wants to run this shell command in their terminal:
COMMAND: `{command}`

Analyze its potential danger. Return ONLY a valid JSON object like:
{{"safe": true, "risk_level": "low", "reason": "brief justification"}}

Be conservative—prioritize alerting user if unsure—but avoid false positives for harmless commands.
"""

        response = pool.chat_with_retry([{"role": "user", "content": prompt}])
        result = response["choices"][0]["message"]["content"].strip()

        # Parse JSON safely instead of using exec()
        result = result.replace("```json", "").replace("```", "").strip()
        parsed = json.loads(result)
        return parsed
    except json.JSONDecodeError:
        console.print(f"[yellow]Warning: Could not parse safety response for '{cmd}'. Blocking as precaution[/yellow]")
        return {"safe": False, "risk_level": "critical", "reason": "Failed to parse safety response"}
    except Exception as e:
        console.print(f"[yellow]Warning: Could not validate dangerous command '{cmd}'. Proceeding anyway[/yellow]")
        return {"safe": False, "risk_level": "critical", "reason": f"Validation failed: {str(e)}"}