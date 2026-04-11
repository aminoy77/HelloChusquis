import json
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table

console = Console()


def detect_complexity(user_input: str, pool) -> bool:
    """Pregunta al LLM si la tarea es simple o compleja."""
    
    # Detecta casos simples sin llamar al LLM
    simple_patterns = [
        "hola", "hello", "hi", "hey", "buenos días", "buenas",
        "gracias", "thanks", "ok", "vale", "sí", "no", "adios",
        "bye", "hasta luego", "qué tal", "cómo estás"
    ]
    if user_input.lower().strip() in simple_patterns:
        return False
    if len(user_input.split()) <= 4:
        return False

    try:
        response = pool.chat_with_retry([
            {
                "role": "system",
                "content": (
                    "You are a task classifier. "
                    "Respond with ONLY one word: 'simple' or 'complex'. "
                    "A task is 'complex' if it requires more than 2 steps, "
                    "multiple tool calls, research, or producing a document/file. "
                    "A task is 'simple' if it's a greeting, question, or single action."
                )
            },
            {"role": "user", "content": user_input}
        ])
        result = response["choices"][0]["message"]["content"].strip().lower()
        return "complex" in result
    except Exception:
        return False
      


def generate_plan(user_input: str, pool) -> list[str]:
    """Pide al LLM que genere un plan de pasos."""
    try:
        response = pool.chat_with_retry([
            {
                "role": "system",
                "content": (
                    "You are a task planner. "
                    "Given a task, respond ONLY with a JSON array of steps. "
                    "Each step is a short action string. Maximum 8 steps. "
                    "Example: [\"Search temperature in Barcelona\", \"Write report to file\"] "
                    "Respond ONLY with the JSON array, nothing else."
                )
            },
            {"role": "user", "content": user_input}
        ])
        content = response["choices"][0]["message"]["content"].strip()
        # Limpia posibles backticks
        content = content.replace("```json", "").replace("```", "").strip()
        steps = json.loads(content)
        return steps if isinstance(steps, list) else []
    except Exception:
        return []


def show_plan(steps: list[str]) -> None:
    table = Table(show_header=False, box=None, padding=(0, 2))
    for i, step in enumerate(steps, 1):
        table.add_row(f"[cyan]{i}.[/cyan]", step)
    console.print(Panel(table, title="[bold]Execution Plan[/bold]", expand=False))


def confirm_plan(steps: list[str], pool, user_input: str) -> list[str] | None:
    """Muestra el plan al user y pide confirmación. Devuelve el plan final o None."""
    while True:
        show_plan(steps)
        console.print("\n[dim]s = execute · n = cancel · e = edit[/dim]")
        choice = Prompt.ask("Proceed?", choices=["s", "n", "e"], default="s")

        if choice == "s":
            return steps
        elif choice == "n":
            console.print("[dim]Plan cancelled.[/dim]")
            return None
        elif choice == "e":
            feedback = Prompt.ask("What should I change?")
            steps = generate_plan(f"{user_input}. Changes requested: {feedback}", pool)
            if not steps:
                console.print("[red]Could not regenerate plan. Try again.[/red]")
                return None


def execute_plan(steps: list[str], agent) -> None:
    """Auto-ejecuta cada paso del plan pasándolo al agente."""
    console.print(f"\n[dim]Executing {len(steps)} steps...[/dim]\n")
    for i, step in enumerate(steps, 1):
        console.print(f"[bold cyan]Step {i}/{len(steps)}:[/bold cyan] {step}")
        try:
            result = agent.run(step)
            from ui.terminal import print_assistant
            print_assistant(result)
        except RuntimeError as e:
            console.print(f"[yellow]⚠ Step {i} failed, skipping...[/yellow]")
            continue
    console.print("\n[green]✓ Plan completed.[/green]")
