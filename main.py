from core.setup import ensure_config
from core.agent import Agent
from rich.console import Console
import signal

console = Console()

# Graceful shutdown flag — checked by main loop
_shutdown_requested = False


def _request_shutdown(signum, frame):
    """Handle SIGTERM/SIGHUP — request graceful shutdown."""
    global _shutdown_requested
    _shutdown_requested = True
    console.print(f"\n[yellow]Signal {signum} received — shutting down gracefully...[/yellow]")


def _cleanup(agent, retention_days):
    """Ensure session and memory are saved on exit."""
    console.print("[dim]Saving session data...[/dim]")
    try:
        agent.summarize_and_save(retention_days)
    except Exception as e:
        console.print(f"[red]Error saving session: {e}[/red]")
    console.print("[dim]Goodbye.[/dim]")


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

    for kw in FORCE_PLAN_KEYWORDS:
        if kw in lower:
            return True

    if len(text.split()) <= 5:
        return False

    if len(text.split()) > 10:
        return True

    return False


def main():
    """Launch HelloChusquis — TUI by default, web/api via subcommands."""
    try:
        config = ensure_config()
    except KeyboardInterrupt:
        console.print("\n[dim]Setup cancelled.[/dim]")
        return 1

    try:
        agent = Agent(config)
    except FileNotFoundError as e:
        console.print("[red]No LLM providers configured. Run 'hellochusquis config' to set up.[/red]")
        console.print(f"[dim]{e}[/dim]")
        return 1
    except Exception as e:
        console.print(f"[red]Failed to initialize agent: {e}[/red]")
        return 1

    retention_days = config["settings"].get("memory_retention_days", 30)

    # Install signal handlers for graceful shutdown
    signal.signal(signal.SIGTERM, _request_shutdown)
    signal.signal(signal.SIGHUP, _request_shutdown)

    # Launch TUI
    from ui.tui import run_tui
    try:
        run_tui(agent=agent, config=config)
    except KeyboardInterrupt:
        pass
    finally:
        _cleanup(agent, retention_days)


if __name__ == "__main__":
    main()
