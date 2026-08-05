"""HelloChusquis terminal UI — opencode-style with left borders."""
from rich.console import Console
from rich.text import Text
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from rich import box
import time

console = Console()

# ─── Palette ───
AMBER = "#f5a623"
GREEN = "#5eb97e"
BLUE = "#7eb8d4"
RED = "#e85d5d"
DIM = "#7e7a70"
MUTED = "#a09a8e"
BORDER = "#1e1d1a"

# ─── State ───
_t0 = 0
_msg_count = 0
_tool_count = 0


def _elapsed():
    s = int(time.time() - _t0)
    m, s = divmod(s, 60)
    return f"{m}m{s}s" if m else f"{s}s"


def _bar():
    """Top bar."""
    console.print(
        f" [bold {AMBER}]⬡[/] [dim]hellochusquis[/] "
        f"  [dim]{_elapsed()}  msgs:{_msg_count}  tools:{_tool_count}[/]"
    )
    console.print(f" [dim]{'─' * 60}[/]")


def print_banner():
    global _t0, _msg_count, _tool_count
    _t0 = time.time()
    _msg_count = 0
    _tool_count = 0
    console.print()
    _bar()
    console.print()


def print_user(message: str):
    global _msg_count
    _msg_count += 1
    console.print()
    # Thick left border like opencode
    console.print(f" [bold {AMBER}]│[/] [bold {AMBER}]you[/]")
    console.print(f" [bold {AMBER}]│[/] {message}")


def print_assistant(message: str):
    if not message:
        return
    global _msg_count
    _msg_count += 1
    console.print()
    console.print(f" [bold {GREEN}]│[/] [bold {GREEN}]agent[/]")
    md = Markdown(message)
    console.print(md, highlight=False)


def print_tool_call(tool: str, params: dict):
    global _tool_count
    _tool_count += 1
    params_str = " ".join(f"{k}={repr(v)}" for k, v in params.items())
    if len(params_str) > 70:
        params_str = params_str[:67] + "..."
    console.print(f" [dim]│[/] [bold {BLUE}]{tool}[/] [dim]{params_str}[/]")


def print_tool_result(success: bool, output: str):
    if not output.strip():
        return
    icon = f"[{GREEN}]✓[/{GREEN}]" if success else f"[{RED}]✗[/{RED}]"
    truncated = output.strip()[:400]
    if len(output.strip()) > 400:
        truncated += "..."
    console.print(f" [dim]│[/] {icon} [dim]{truncated}[/]")


def print_error(message: str):
    console.print()
    console.print(f" [bold {RED}]│[/] [bold {RED}]error[/] {message}")


def print_status(providers: list[dict]):
    console.print()
    table = Table(box=box.SIMPLE, border_style=BORDER, show_header=True, padding=(0, 1))
    table.add_column("", width=3)
    table.add_column("Provider", style="bold")
    table.add_column("Model", style="dim")
    table.add_column("Latency", justify="right", style="dim")
    table.add_column("Calls", justify="right", style="dim")
    for p in providers:
        color = GREEN if p["status"] == "ready" else RED
        icon = f"[{color}]●[/{color}]"
        latency = f"{p.get('avg_ms', '—')}ms" if p.get("avg_ms") else "—"
        table.add_row(icon, p["name"], p["model"], latency, str(p.get("calls", 0)))
    console.print(table)


def print_plan(steps: list[str], task: str):
    console.print()
    console.print(f" [bold {AMBER}]│[/] [bold {AMBER}]plan[/] {task}")
    for i, step in enumerate(steps, 1):
        console.print(f" [dim]│[/]  {i}. {step}")


def print_plan_result(success: bool, summary: str):
    icon = f"[{GREEN}]✓[/{GREEN}]" if success else f"[{RED}]✗[/{RED}]"
    console.print(f" [bold {GREEN}]│[/] {icon} {summary}")


def get_input() -> str:
    console.print()
    try:
        from rich.prompt import Prompt
        return Prompt.ask(f"[bold {AMBER}]you[/]")
    except (KeyboardInterrupt, EOFError):
        return "exit"
