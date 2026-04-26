from core.setup import ensure_config
from ui.terminal import print_assistant, print_banner, get_input, print_status
from core.agent import Agent
from core.planner import generate_plan, confirm_plan, execute_plan
from core.learning import add_feedback
from core.command_palette import open_palette
from rich.console import Console
import threading
import sys

console = Console()

# Palabras que siempre son tareas complejas — sin llamar al LLM
FORCE_PLAN_KEYWORDS = [
    "informe", "report", "analiza", "analyze", "investiga", "research",
    "crea un pdf", "crea un word", "crea un documento", "haz un estudio",
    "busca y", "busca las", "compara", "compare", "cada", "every",
    "paso a paso", "step by step", "lista de", "plan de"
]

# Palabras que siempre son simples — sin llamar al LLM
FORCE_SIMPLE_KEYWORDS = [
    "hola", "hello", "hi", "hey", "gracias", "thanks", "ok", "vale",
    "sí", "no", "adios", "bye", "qué tal", "cómo estás", "buenas"
]


def is_complex(text: str) -> bool:
    """Detecta complejidad SIN llamar al LLM — instant."""
    lower = text.lower().strip()

    if lower in FORCE_SIMPLE_KEYWORDS:
        return False

    if len(text.split()) <= 5:
        return False

    for kw in FORCE_PLAN_KEYWORDS:
        if kw in lower:
            return True

    # Solo llama al LLM si tiene más de 10 palabras y no es claramente simple
    if len(text.split()) > 10:
        return True

    return False


def handle_feedback(user_input: str, history):
    if user_input in ["👍", "+", "good", "bien"]:
        msgs = history.get()
        ctx = msgs[-2]["content"] if len(msgs) >= 2 else ""
        add_feedback("positive", ctx)
        console.print("[green]✓ Feedback saved[/green]")
        return True
    if user_input in ["👎", "-", "bad", "mal"]:
        msgs = history.get()
        ctx = msgs[-2]["content"] if len(msgs) >= 2 else ""
        add_feedback("negative", ctx)
        console.print("[red]✓ Feedback saved[/red]")
        return True
    return False


def handle_command_palette(agent):
    """Open command palette."""
    try:
        from core.command_palette import open_palette
        console.print("\n[dim]Opening command palette... (Ctrl+C to exit)[/dim]\n")
        open_palette(agent)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        console.print(f"[red]Command palette error: {e}[/red]")


def main():
    config = ensure_config()
    agent = Agent(config)
    retention_days = config["settings"].get("memory_retention_days", 30)

    print_banner()
    try:
        user_input = get_input()
        while user_input not in ["exit", "quit"]:

            if handle_feedback(user_input, agent.history):
                user_input = get_input()
                continue

            if user_input == "/help":
                console.print("""
[bold #f5a623]HelloChusquis Commands[/bold #f5a623]

[bold]Chat:[/bold]
  /help      — Show this help
  /palette  — Open command palette (Ctrl+P)
  /status    — Provider status
  /clear     — Clear history
  /plan      — Force plan: /plan <task>
  👍 / +     — Positive feedback
  👎 / -     — Negative feedback
  exit       — Exit

[bold]Terminal:[/bold]
  hellochusquis install <plugin>
  hellochusquis uninstall <plugin>
  hellochusquis plugins
  hellochusquis build
  hellochusquis learn
  hellochusquis web
  hellochusquis daemon [start|stop|status|install|add|tasks|log]
""")

            elif user_input == "/status":
                statuses = agent.pool.status()
                print_status(statuses)
                for s in statuses:
                    if s.get("avg_ms"):
                        console.print(f"  [dim]avg {s['avg_ms']}ms · {s['calls']} calls · {s['failures']} failures[/dim]")

            elif user_input == "/clear":
                agent.history.clear()
                console.print("[dim]History cleared.[/dim]")

            elif user_input == "/palette":
                handle_command_palette(agent)

            elif user_input.startswith("/plan "):
                task = user_input[6:].strip()
                steps = generate_plan(task, agent.pool)
                if steps:
                    final = confirm_plan(steps, agent.pool, task)
                    if final:
                        execute_plan(final, agent)
                else:
                    console.print("[red]Could not generate plan.[/red]")

            elif user_input.strip() == "":
                pass

            else:
                try:
                    if is_complex(user_input):
                        console.print("[dim]Complex task — generating plan...[/dim]")
                        steps = generate_plan(user_input, agent.pool)
                        if steps:
                            final = confirm_plan(steps, agent.pool, user_input)
                            if final:
                                execute_plan(final, agent)
                        else:
                            respuesta = agent.run(user_input)
                            print_assistant(respuesta)
                    else:
                        respuesta = agent.run(user_input)
                        print_assistant(respuesta)
                        console.print("[dim]  👍 / 👎[/dim]")

                except RuntimeError as e:
                    console.print(f"\n[red]✗ {e}[/red]")
                    console.print("[dim]Add more providers: rm config.yaml && hellochusquis[/dim]")

            user_input = get_input()

    except KeyboardInterrupt:
        console.print("\n")

    console.print("[dim]Saving memory...[/dim]")
    agent.summarize_and_save(retention_days)
    console.print("[dim]Goodbye.[/dim]")


if __name__ == "__main__":
    main()