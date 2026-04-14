from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt
from rich.markdown import Markdown

console = Console()


def print_banner():
    console.print(Panel(
        "[bold #f5a623]HelloChusquis[/bold #f5a623] [dim]terminal AI agent[/dim]",
        expand=False,
        border_style="#1f1e1b"
    ))


def print_user(message: str):
    console.print(f"\n[bold white]You[/bold white]: {message}")


def print_assistant(message: str):
    console.print(f"\n[bold #f5a623]HelloChusquis[/bold #f5a623]:")
    console.print(Markdown(message))


def print_tool_call(tool: str, params: dict):
    params_str = " ".join(f"{k}={repr(v)}" for k, v in params.items())
    console.print(f"\n[dim]→ {tool}({params_str})[/dim]")


def print_tool_result(success: bool, output: str):
    if output.strip():
        icon = "[#5eb97e]✓[/#5eb97e]" if success else "[red]✗[/red]"
        console.print(f"{icon} [dim]{output.strip()[:500]}[/dim]")


def print_error(message: str):
    console.print(f"\n[red]Error:[/red] {message}")


def print_status(providers: list[dict]):
    console.print("\n[bold #f5a623]Provider status:[/bold #f5a623]")
    for p in providers:
        color = "#5eb97e" if p["status"] == "ready" else "red"
        console.print(f"  [{color}]●[/{color}] {p['name']} — {p['model']}")


def get_input() -> str:
    return Prompt.ask("\n[bold white]You[/bold white]")