from pathlib import Path
from rich.prompt import Confirm
from rich.console import Console

console = Console()


class WorkspaceManager:
    def __init__(self, initial_dirs: list[str]):
        self.allowed = [Path(d).expanduser().resolve() for d in initial_dirs]

    def is_allowed(self, path: str) -> bool:
        p = Path(path).expanduser().resolve()
        return any(p == d or d in p.parents for d in self.allowed)

    def request_access(self, path: str) -> bool:
        p = Path(path).expanduser().resolve()
        if self.is_allowed(path):
            return True
        console.print(f"\n[yellow]⚠ HelloChusquis wants access to:[/yellow] {p}")
        granted = Confirm.ask("Allow?", default=False)
        if granted:
            self.allowed.append(p)
            console.print(f"[green]✓ Access granted[/green]")
        else:
            console.print(f"[red]✗ Access denied[/red]")
        return granted

    def list_allowed(self) -> list[str]:
        return [str(d) for d in self.allowed]