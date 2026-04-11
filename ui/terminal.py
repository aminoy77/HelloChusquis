from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt
from rich.markdown import Markdown

console = Console()


def print_banner():
    console.print(Panel(
        "[bold cyan]HelloChusquis[/bold cyan] [dim]terminal AI agent[/dim]",
        expand=False
    ))


def print_user(message: str):
    console.print(f"\n[bold cyan]You[/bold cyan]: {message}")


def print_assistant(message: str):
    console.print(f"\n[bold green]HelloChusquis[/bold green]:")
    console.print(Markdown(message))


def print_tool_call(tool: str, params: dict):
    params_str = " ".join(f"{k}={repr(v)}" for k, v in params.items())
    console.print(f"\n[dim]→ {tool}({params_str})[/dim]")


def print_tool_result(success: bool, output: str):
    if output.strip():
        icon = "[green]✓[/green]" if success else "[red]✗[/red]"
        console.print(f"{icon} [dim]{output.strip()[:500]}[/dim]")


def print_error(message: str):
    console.print(f"\n[red]Error:[/red] {message}")


def print_status(providers: list[dict]):
    console.print("\n[bold]Provider status:[/bold]")
    for p in providers:
        color = "green" if p["status"] == "ready" else "red"
        console.print(f"  [{color}]●[/{color}] {p['name']} — {p['model']}")


def get_input() -> str:
    return Prompt.ask("\n[bold cyan]You[/bold cyan]")

def print_status(providers: list[dict]):
    console.print("\n[bold]Provider status:[/bold]")
    for p in providers:
        color = "green" if p["status"] == "ready" else "red"
        icon = "●" if p["status"] == "ready" else "○"
        console.print(f"  [{color}]{icon}[/{color}] {p['name']} — [cyan]{p['model']}[/cyan] [{color}]{p['status']}[/{color}]")
    console.print()
